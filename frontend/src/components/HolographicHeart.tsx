import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

interface HolographicHeartProps {
  status?: 'idle' | 'loading' | 'verified' | 'warning';
  bpm?: number;
  className?: string;
}

export const HolographicHeart = ({
  status = 'idle',
  bpm: initialBpm,
  className = '',
}: HolographicHeartProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isInteracting, setIsInteracting] = useState(false);

  const bpm = initialBpm || (status === 'loading' ? 108 : status === 'warning' ? 88 : 72);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    // 1. Scene, Camera, Renderer
    const width = container.clientWidth || 380;
    const height = container.clientHeight || 380;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 2, 42);

    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Colors matching Dark Neon Healthcare theme
    const emeraldColor = new THREE.Color(0x10b981);
    const cyanColor = new THREE.Color(0x00f5d4);
    const alertColor = new THREE.Color(0xf59e0b);

    const activeColor = status === 'warning' ? alertColor : status === 'loading' ? cyanColor : emeraldColor;

    // 2. Heart Particle Geometry Generator (Parametric 3D Anatomical Heart Shape)
    const particleCount = 2800;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const baseScales = new Float32Array(particleCount);

    let idx = 0;
    for (let i = 0; i < particleCount; i++) {
      // Stratified angle distribution
      const u = Math.PI * 2 * Math.random();

      // Parametric 3D heart formulation
      // x = 16 * sin^3(t) * sin(u)
      // y = (13 * cos(t) - 5 * cos(2t) - 2 * cos(3t) - cos(4t))
      // z = 16 * sin^3(t) * cos(u)
      const t = Math.PI * (Math.random() * 2 - 1);
      const sinT = Math.sin(t);
      const cosT = Math.cos(t);

      // Heart surface coordinate
      let x = 16 * Math.pow(sinT, 3);
      let y = 13 * cosT - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t);
      let z = 16 * Math.pow(sinT, 3) * Math.sin(u) * 0.75;

      // Add volumetric distribution and aorta vessel accents
      const isAorta = i > particleCount - 250;
      if (isAorta) {
        // Arching aorta tubes at top
        const archT = (i - (particleCount - 250)) / 250;
        const archAngle = archT * Math.PI * 1.2;
        x = Math.sin(archAngle) * 4.5 - 2;
        y = 12 + Math.cos(archAngle) * 4 + (Math.random() - 0.5) * 1.5;
        z = (Math.random() - 0.5) * 4;
      } else {
        // Internal volume scatter with depth
        const depthFactor = 0.75 + Math.random() * 0.35;
        x *= depthFactor;
        y *= depthFactor;
        z *= depthFactor;
      }

      // Scaling down to scene units
      const scale = 0.7;
      positions[idx * 3] = x * scale;
      positions[idx * 3 + 1] = (y - 2) * scale;
      positions[idx * 3 + 2] = z * scale;

      // Color gradient: blend cyan at top (vessels) to deep emerald at apex
      const heightRatio = (y + 15) / 30;
      const pointColor = new THREE.Color().lerpColors(emeraldColor, activeColor, heightRatio);

      colors[idx * 3] = pointColor.r;
      colors[idx * 3 + 1] = pointColor.g;
      colors[idx * 3 + 2] = pointColor.b;

      baseScales[idx] = Math.random() * 1.5 + 0.8;
      idx++;
    }

    const heartGeometry = new THREE.BufferGeometry();
    heartGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    heartGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // Particle Material with Soft Glow Sprite
    const canvasTexture = document.createElement('canvas');
    canvasTexture.width = 32;
    canvasTexture.height = 32;
    const ctx = canvasTexture.getContext('2d');
    if (ctx) {
      const gradient = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
      gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
      gradient.addColorStop(0.25, 'rgba(0, 245, 212, 0.85)');
      gradient.addColorStop(0.7, 'rgba(16, 185, 129, 0.25)');
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 32, 32);
    }
    const particleTexture = new THREE.CanvasTexture(canvasTexture);

    const heartMaterial = new THREE.PointsMaterial({
      size: 0.9,
      map: particleTexture,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const heartPoints = new THREE.Points(heartGeometry, heartMaterial);
    scene.add(heartPoints);

    // 3. Inner Holographic Lattice Cage
    const cageGeometry = new THREE.IcosahedronGeometry(7.5, 2);
    const cageWireframe = new THREE.WireframeGeometry(cageGeometry);
    const cageLineMaterial = new THREE.LineBasicMaterial({
      color: activeColor,
      transparent: true,
      opacity: 0.18,
      blending: THREE.AdditiveBlending,
    });
    const cageLines = new THREE.LineSegments(cageWireframe, cageLineMaterial);
    cageLines.scale.set(0.9, 1.15, 0.85);
    cageLines.position.set(0, -1, 0);
    scene.add(cageLines);

    // 4. Orbital Holographic Telemetry Rings
    const createRing = (radius: number, tiltX: number, tiltY: number, color: THREE.Color, speed: number) => {
      const ringGeom = new THREE.RingGeometry(radius - 0.08, radius + 0.08, 64);
      const ringMat = new THREE.MeshBasicMaterial({
        color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.35,
        blending: THREE.AdditiveBlending,
      });
      const ringMesh = new THREE.Mesh(ringGeom, ringMat);
      ringMesh.rotation.x = tiltX;
      ringMesh.rotation.y = tiltY;
      scene.add(ringMesh);
      return { mesh: ringMesh, speed };
    };

    const rings = [
      createRing(14, Math.PI / 3, 0.2, cyanColor, 0.008),
      createRing(15.5, -Math.PI / 4, 0.5, emeraldColor, -0.006),
      createRing(17, Math.PI / 6, -0.3, activeColor, 0.01),
    ];

    // 5. Ambient Floating Bio-Dust Field
    const dustCount = 180;
    const dustPositions = new Float32Array(dustCount * 3);
    for (let i = 0; i < dustCount * 3; i += 3) {
      dustPositions[i] = (Math.random() - 0.5) * 55;
      dustPositions[i + 1] = (Math.random() - 0.5) * 55;
      dustPositions[i + 2] = (Math.random() - 0.5) * 45;
    }
    const dustGeometry = new THREE.BufferGeometry();
    dustGeometry.setAttribute('position', new THREE.BufferAttribute(dustPositions, 3));
    const dustMaterial = new THREE.PointsMaterial({
      size: 0.45,
      map: particleTexture,
      color: cyanColor,
      transparent: true,
      opacity: 0.45,
      blending: THREE.AdditiveBlending,
    });
    const dustPoints = new THREE.Points(dustGeometry, dustMaterial);
    scene.add(dustPoints);

    // Mouse Interaction
    let targetRotationX = 0;
    let targetRotationY = 0;
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;

    const handlePointerDown = (e: MouseEvent) => {
      isDragging = true;
      setIsInteracting(true);
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const handlePointerMove = (e: MouseEvent) => {
      if (isDragging) {
        const deltaX = e.clientX - prevMouseX;
        const deltaY = e.clientY - prevMouseY;
        targetRotationY += deltaX * 0.008;
        targetRotationX += deltaY * 0.008;
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
      }
    };

    const handlePointerUp = () => {
      isDragging = false;
      setIsInteracting(false);
    };

    canvas.addEventListener('mousedown', handlePointerDown);
    window.addEventListener('mousemove', handlePointerMove);
    window.addEventListener('mouseup', handlePointerUp);

    // 6. Animation Loop (Cardiac Rhythm)
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();
      const currentBpm = status === 'loading' ? 112 : status === 'warning' ? 88 : 72;
      const freq = (currentBpm / 60) * Math.PI * 2;

      // Realistic cardiac cycle: ventricular systole (contract) followed by diastolic refill
      // Asymmetric sine pulse
      const phase = (elapsedTime * freq) % (Math.PI * 2);
      let cardiacScale = 1.0;
      if (phase < Math.PI * 0.35) {
        // Quick systolic contraction / expansion
        cardiacScale = 1.0 + Math.sin((phase / (Math.PI * 0.35)) * Math.PI) * 0.085;
      } else if (phase < Math.PI * 0.65) {
        // Secondary atria recoil
        const subPhase = (phase - Math.PI * 0.35) / (Math.PI * 0.3);
        cardiacScale = 1.0 + Math.sin(subPhase * Math.PI) * 0.04;
      }

      // Smooth damped rotation
      heartPoints.rotation.y += (targetRotationY - heartPoints.rotation.y) * 0.05 + 0.0035;
      heartPoints.rotation.x += (targetRotationX - heartPoints.rotation.x) * 0.05;
      heartPoints.scale.set(cardiacScale, cardiacScale, cardiacScale);

      cageLines.rotation.y = heartPoints.rotation.y * 0.8;
      cageLines.rotation.x = heartPoints.rotation.x * 0.8;
      cageLines.scale.set(cardiacScale * 0.9, cardiacScale * 1.12, cardiacScale * 0.85);

      // Rotate rings
      rings.forEach((r, rIdx) => {
        r.mesh.rotation.z += r.speed;
        r.mesh.rotation.y += r.speed * 0.5;
        r.mesh.scale.set(
          1 + Math.sin(elapsedTime * 2 + rIdx) * 0.02,
          1 + Math.sin(elapsedTime * 2 + rIdx) * 0.02,
          1
        );
      });

      // Slowly rotate dust
      dustPoints.rotation.y = elapsedTime * 0.015;

      renderer.render(scene, camera);
    };

    animate();

    // 7. Responsive Resizing
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const newW = container.clientWidth;
      const newH = container.clientHeight;
      if (newW > 0 && newH > 0) {
        camera.aspect = newW / newH;
        camera.updateProjectionMatrix();
        renderer.setSize(newW, newH);
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      canvas.removeEventListener('mousedown', handlePointerDown);
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('mouseup', handlePointerUp);

      heartGeometry.dispose();
      heartMaterial.dispose();
      particleTexture.dispose();
      cageGeometry.dispose();
      cageWireframe.dispose();
      cageLineMaterial.dispose();
      dustGeometry.dispose();
      dustMaterial.dispose();
      renderer.dispose();
    };
  }, [status]);

  return (
    <div
      ref={containerRef}
      className={`holographic-heart-container ${className}`}
      title="Interactive 3D Holographic Heart — Drag to rotate"
    >
      <canvas ref={canvasRef} className="holographic-heart-canvas" />

      {/* Futuristic Telemetry Overlay Badges */}
      <div className="heart-telemetry-badge top-left">
        <span className="telemetry-label">CARDIAC RHYTHM</span>
        <span className="telemetry-value">
          <span className="pulse-dot"></span>
          {bpm} BPM
        </span>
      </div>

      <div className="heart-telemetry-badge top-right">
        <span className="telemetry-label">PIPELINE MONITOR</span>
        <span className={`telemetry-status-pill ${status}`}>
          {status === 'loading'
            ? 'RETRIEVING…'
            : status === 'warning'
            ? 'HALLUCINATION CHECK'
            : 'CLINICAL GROUNDED'}
        </span>
      </div>

      <div className="heart-telemetry-badge bottom-center">
        <span className="telemetry-hint">
          {isInteracting ? 'ROTATING VIEW' : 'CLICK & DRAG TO ROTATE 3D HOLOGRAM'}
        </span>
      </div>
    </div>
  );
};
