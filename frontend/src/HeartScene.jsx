import { Component, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { ContactShadows, Environment, Html, Lightformer, OrbitControls, useGLTF, useProgress } from '@react-three/drei';
import * as THREE from 'three';
import { ARTERIES } from './config/arteries';

/**
 * 3D heart model location.
 * Put your .glb at  frontend/public/models/heart.glb
 * (or point VITE_HEART_MODEL_URL in frontend/.env to another path / URL).
 */
const MODEL_URL = import.meta.env.VITE_HEART_MODEL_URL || `${import.meta.env.BASE_URL}models/heart.glb`;

/** Height (scene units) the supplied model is normalised to. The artery overlay is authored for ~1.5. */
const MODEL_HEIGHT = 1.5;

/**
 * The artery overlay was authored with the left/right axis mirrored relative to the supplied
 * anatomical model (apex toward +X as seen from the front). Mirror X and nudge the overlay slightly
 * forward so it sits in front of the cut-away surface. Data in config/arteries.js is untouched.
 */
const fit = ([x, y, z]) => [-x, y, z + 0.08];
const FITTED_ARTERIES = ARTERIES.map((a) => ({
  ...a,
  points: a.points.map(fit),
  branches: (a.branches || []).map((b) => b.map(fit)),
}));

function riskColor(p = 0) {
  const t = Math.min(1, Math.max(0, p));
  if (t < 0.5) {
    return new THREE.Color('#2f9f72').lerp(new THREE.Color('#d8a63a'), t / 0.5);
  }
  return new THREE.Color('#d8a63a').lerp(new THREE.Color('#d94b4b'), (t - 0.5) / 0.5);
}

function variableTubeGeometry(curve, tubularSegments, radialSegments, radiusFn) {
  const frames = curve.computeFrenetFrames(tubularSegments, false);
  const positions = [];
  const normals = [];
  const uvs = [];
  const indices = [];
  for (let i = 0; i <= tubularSegments; i += 1) {
    const u = i / tubularSegments;
    const p = curve.getPointAt(u);
    const N = frames.normals[i];
    const B = frames.binormals[i];
    const radius = radiusFn(u);
    for (let j = 0; j <= radialSegments; j += 1) {
      const v = (j / radialSegments) * Math.PI * 2;
      const sin = Math.sin(v);
      const cos = Math.cos(v);
      const cx = -radius * (cos * N.x + sin * B.x);
      const cy = -radius * (cos * N.y + sin * B.y);
      const cz = -radius * (cos * N.z + sin * B.z);
      positions.push(p.x + cx, p.y + cy, p.z + cz);
      const len = Math.hypot(cx, cy, cz) || 1;
      normals.push(cx / len, cy / len, cz / len);
      uvs.push(u, j / radialSegments);
    }
  }
  for (let i = 0; i < tubularSegments; i += 1) {
    for (let j = 0; j < radialSegments; j += 1) {
      const a = i * (radialSegments + 1) + j;
      const b = a + radialSegments + 1;
      indices.push(a, b, a + 1, b, b + 1, a + 1);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setIndex(indices);
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  return geo;
}

function makeHeartGeometry() {
  const geo = new THREE.SphereGeometry(0.78, 28, 22);
  const pos = geo.attributes.position;
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i += 1) {
    v.fromBufferAttribute(pos, i);
    const x = v.x;
    const y = v.y;
    const bulge = 0.18 * Math.exp(-((x - 0.22) ** 2 + (y - 0.28) ** 2) / 0.22);
    const bulgeL = 0.2 * Math.exp(-((x + 0.24) ** 2 + (y - 0.26) ** 2) / 0.2);
    const waist = 1 + 0.12 * Math.sin((y + 0.2) * 1.6);
    const tip = y < -0.15 ? 1 + (-0.15 - y) * 0.35 : 1;
    v.x *= waist * 0.86;
    v.z *= waist * 0.78;
    v.y = v.y * 1.12 * tip + 0.04;
    v.x += Math.sign(x || 1) * (bulge + bulgeL) * 0.35;
    v.y += bulge + bulgeL * 0.8;
    pos.setXYZ(i, v.x, v.y, v.z);
  }
  geo.computeVertexNormals();
  return geo;
}

/** Supplied model: geometry, textures and materials are used exactly as exported. */
function GlbHeart({ url }) {
  const gltf = useGLTF(url);
  const scene = useMemo(() => {
    const cloned = gltf.scene.clone(true);
    const box = new THREE.Box3().setFromObject(cloned);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    cloned.position.sub(center);
    const wrapper = new THREE.Group();
    wrapper.add(cloned);
    wrapper.scale.setScalar(MODEL_HEIGHT / (size.y || 1));
    return wrapper;
  }, [gltf]);
  return <primitive object={scene} />;
}

/** Only used when the supplied model cannot be loaded (a notice is shown to the user). */
function ProceduralHeart() {
  const geo = useMemo(() => makeHeartGeometry(), []);
  return (
    <mesh geometry={geo}>
      <meshStandardMaterial color="#b03a52" transparent opacity={0.5} roughness={0.48} metalness={0.04} depthWrite={false} />
    </mesh>
  );
}

class SceneErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error) {
    console.error(this.props.label || '3D scene error:', error);
    this.props.onError?.(error);
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

function Artery({ spec, probability = 0.2, selected, hovered, onHover, onSelect }) {
  const color = riskColor(probability);
  const curve = useMemo(
    () => new THREE.CatmullRomCurve3(spec.points.map((p) => new THREE.Vector3(...p))),
    [spec],
  );
  const stenosisT = spec.stenosisT ?? 0.5;
  const geo = useMemo(() => {
    const radiusFn = (u) => {
      const base = 0.028 + (1 - probability) * 0.012;
      const dip = Math.exp(-((u - stenosisT) ** 2) / 0.012) * probability * 0.018;
      return Math.max(0.008, base - dip);
    };
    return variableTubeGeometry(curve, 48, 8, radiusFn);
  }, [curve, probability, stenosisT]);
  const branchGeos = useMemo(
    () =>
      (spec.branches || []).map((pts) => {
        const c = new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(...p)));
        return new THREE.TubeGeometry(c, 16, 0.01, 6, false);
      }),
    [spec],
  );
  useEffect(
    () => () => {
      geo.dispose();
      branchGeos.forEach((g) => g.dispose());
    },
    [geo, branchGeos],
  );
  const glow = probability >= 0.7;
  const mid = curve.getPointAt(0.55);
  return (
    <group>
      <mesh
        geometry={geo}
        onPointerOver={(e) => {
          e.stopPropagation();
          onHover(spec.id);
        }}
        onPointerOut={() => onHover(null)}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(spec.id);
        }}
      >
        <meshStandardMaterial
          color={hovered || selected ? '#ffffff' : color}
          emissive={glow ? color : '#000000'}
          emissiveIntensity={glow ? 0.45 : hovered ? 0.2 : 0}
          roughness={0.35}
          metalness={0.15}
        />
      </mesh>
      {branchGeos.map((g, i) => (
        <mesh key={i} geometry={g}>
          <meshStandardMaterial color={color} roughness={0.4} />
        </mesh>
      ))}
      <Html position={[mid.x, mid.y + 0.08, mid.z]} center distanceFactor={2} style={{ pointerEvents: 'none' }}>
        <div className={`callout ${selected ? 'active' : ''}`}>
          <span className="calloutIcon">{spec.icon}</span>
          {spec.label} {Math.round(probability * 100)}%
        </div>
      </Html>
    </group>
  );
}

function CameraRig({ focusId, controlsRef }) {
  const { camera } = useThree();
  const target = useMemo(() => {
    const spec = FITTED_ARTERIES.find((a) => a.id === focusId);
    if (!spec) return new THREE.Vector3(0, 0, 0);
    const curve = new THREE.CatmullRomCurve3(spec.points.map((p) => new THREE.Vector3(...p)));
    return curve.getPointAt(0.55);
  }, [focusId]);
  useFrame((_, dt) => {
    if (!focusId) return;
    const desired = target.clone().add(new THREE.Vector3(0.9, 0.6, 1.9));
    camera.position.lerp(desired, 1 - Math.exp(-2.2 * dt));
    controlsRef.current?.target.lerp(target, 1 - Math.exp(-2.2 * dt));
  });
  return null;
}

function PulseGroup({ pulseRate, enabled, children }) {
  const ref = useRef();
  useFrame(({ clock }) => {
    if (!ref.current) return;
    if (!enabled) {
      ref.current.scale.setScalar(1);
      return;
    }
    const bpm = Math.max(40, Math.min(140, Number(pulseRate) || 76));
    const s = 1 + 0.018 * Math.sin(clock.elapsedTime * (bpm / 60) * Math.PI * 2);
    ref.current.scale.setScalar(s);
  });
  return <group ref={ref}>{children}</group>;
}

/** Soft studio lighting generated in code (no network / HDR download needed). */
function Studio() {
  return (
    <Environment resolution={256} frames={1}>
      <Lightformer form="rect" intensity={2.2} position={[0, 4, 3]} scale={[8, 3, 1]} color="#ffffff" />
      <Lightformer form="rect" intensity={1.2} position={[-4, 1, 2]} scale={[3, 5, 1]} color="#ffe3ea" />
      <Lightformer form="rect" intensity={1.0} position={[4, 0.5, -2]} scale={[3, 5, 1]} color="#e6dcff" />
      <Lightformer form="ring" intensity={1.4} position={[0, -3, 2]} scale={4} color="#fff2e6" />
    </Environment>
  );
}

function LoadingOverlay() {
  const { active, progress } = useProgress();
  if (!active) return null;
  return (
    <div className="sceneLoading" role="status" aria-live="polite">
      <div className="loadHeart" aria-hidden="true">♥</div>
      <div className="loadBar">
        <i style={{ width: `${Math.max(6, Math.round(progress))}%` }} />
      </div>
      <span>Loading 3D heart… {Math.round(progress)}%</span>
    </div>
  );
}

export function HeartScene({
  prediction,
  selected,
  onSelect,
  pulseRate = 76,
  pulseOn = true,
  autoRotate = false,
}) {
  const controlsRef = useRef();
  const stageRef = useRef();
  const [hovered, setHovered] = useState(null);
  const [focusId, setFocusId] = useState(null);
  const [modelFailed, setModelFailed] = useState(false);
  const [visible, setVisible] = useState(true);

  function select(id) {
    onSelect(id);
    setFocusId(id);
  }

  useEffect(() => {
    setFocusId(selected === 'cad' ? null : selected);
  }, [selected]);

  // Pause rendering while the stage is scrolled out of view (saves GPU/battery).
  useEffect(() => {
    const el = stageRef.current;
    if (!el || typeof IntersectionObserver === 'undefined') return undefined;
    const io = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting), { threshold: 0.05 });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div className="heartStage" ref={stageRef}>
      <div className="stageGlow" aria-hidden="true" />
      <div className="sceneTitle">3D coronary risk map</div>
      <div className="sceneHint" aria-hidden="true">Drag to rotate · Scroll / pinch to zoom</div>

      <SceneErrorBoundary
        label="3D view could not start:"
        fallback={<div className="sceneFallback">3D view is not available on this device or browser (WebGL could not start).</div>}
      >
        <Canvas
          dpr={[1, 1.5]}
          frameloop={visible ? 'always' : 'never'}
          camera={{ position: [0.2, 0.25, 3.0], fov: 40 }}
          gl={{ antialias: true, powerPreference: 'high-performance', alpha: true }}
          style={{ background: 'transparent' }}
        >
          <ambientLight intensity={0.55} />
          <directionalLight position={[2.2, 2.6, 2.4]} intensity={1.1} />
          <directionalLight position={[-2.4, 0.6, -1.6]} intensity={0.4} color="#ffd9e2" />
          <Suspense fallback={null}>
            <Studio />
          </Suspense>
          <PulseGroup pulseRate={pulseRate} enabled={pulseOn}>
            <SceneErrorBoundary
              label="Heart model failed to load:"
              onError={() => setModelFailed(true)}
              fallback={<ProceduralHeart />}
            >
              <Suspense fallback={null}>
                <GlbHeart url={MODEL_URL} />
              </Suspense>
            </SceneErrorBoundary>
            {FITTED_ARTERIES.map((spec) => (
              <Artery
                key={spec.id}
                spec={spec}
                probability={prediction?.targets?.[spec.id]?.probability || 0.15}
                selected={selected === spec.id}
                hovered={hovered === spec.id}
                onHover={setHovered}
                onSelect={select}
              />
            ))}
          </PulseGroup>
          <ContactShadows position={[0, -0.92, 0]} opacity={0.28} scale={4.2} blur={2.8} far={1.6} frames={1} color="#6b2a45" />
          <CameraRig focusId={focusId} controlsRef={controlsRef} />
          <OrbitControls
            ref={controlsRef}
            enableDamping
            dampingFactor={0.08}
            enablePan={false}
            autoRotate={autoRotate}
            autoRotateSpeed={1.1}
            minDistance={1.4}
            maxDistance={5}
            onStart={() => setFocusId(null)}
          />
        </Canvas>
      </SceneErrorBoundary>

      <LoadingOverlay />

      {modelFailed && (
        <div className="sceneNotice" role="alert">
          Heart model not found at <code>public/models/heart.glb</code> — showing a simplified placeholder.
        </div>
      )}

      {hovered && (
        <div className="tooltip">
          {ARTERIES.find((a) => a.id === hovered)?.fullName}:{' '}
          {Math.round((prediction?.targets?.[hovered]?.probability || 0) * 100)}% stenosis probability
        </div>
      )}
      <div className="sceneActions">
        <button
          type="button"
          onClick={() => {
            setFocusId(null);
            controlsRef.current?.reset();
          }}
        >
          Reset camera
        </button>
        <span className="legend">
          <i className="g" /> low <i className="y" /> mid <i className="r" /> high · narrowing = stenosis probability
        </span>
      </div>
    </div>
  );
}

export function startGuidedRotation(setAuto) {
  setAuto(true);
}
