import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';

export type HeartStatus = 'idle' | 'loading' | 'verified' | 'contradicted' | 'warning' | 'error';

interface HolographicHeartProps {
  status?: HeartStatus;
  latencyMs?: number | null;
  confidenceLevel?: 'HIGH' | 'MEDIUM' | 'LOW' | null;
  isCorrected?: boolean;
  className?: string;
}

// Check if WebGL context can be created
function isWebGLAvailable(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return Boolean(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    );
  } catch {
    return false;
  }
}

export const HolographicHeart: React.FC<HolographicHeartProps> = ({
  status = 'idle',
  latencyMs,
  confidenceLevel,
  isCorrected = false,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isInteracting, setIsInteracting] = useState(false);
  const [webGLSupported, setWebGLSupported] = useState<boolean>(() => isWebGLAvailable());
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  // Rotation angles tracked for both mouse and keyboard interactions
  const rotationRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });

  // Listen to prefers-reduced-motion media query changes
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // Reset rotation to initial front-facing orientation
  const handleResetOrientation = useCallback(() => {
    rotationRef.current.targetX = 0;
    rotationRef.current.targetY = 0;
  }, []);

  // Keyboard navigation for accessible 3D manipulation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const step = 0.1;
    switch (e.key) {
      case 'ArrowLeft':
        e.preventDefault();
        rotationRef.current.targetY -= step;
        setIsInteracting(true);
        break;
      case 'ArrowRight':
        e.preventDefault();
        rotationRef.current.targetY += step;
        setIsInteracting(true);
        break;
      case 'ArrowUp':
        e.preventDefault();
        rotationRef.current.targetX -= step;
        setIsInteracting(true);
        break;
      case 'ArrowDown':
        e.preventDefault();
        rotationRef.current.targetX += step;
        setIsInteracting(true);
        break;
      case 'r':
      case 'R':
      case ' ':
        e.preventDefault();
        handleResetOrientation();
        setIsInteracting(false);
        break;
      default:
        break;
    }
  };

  useEffect(() => {
    if (!webGLSupported) return;

    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    // 1. Scene, Camera, Renderer
    const width = container.clientWidth || 360;
    const height = container.clientHeight || 360;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 1.5, 40);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance',
      });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    } catch {
      requestAnimationFrame(() => {
        setWebGLSupported(false);
      });
      return;
    }

    // Palette mapped to verified application state
    const emeraldColor = new THREE.Color(0x10b981);
    const cyanColor = new THREE.Color(0x00f5d4);
    const amberColor = new THREE.Color(0xf59e0b);
    const alertColor = new THREE.Color(0xef4444);

    let primaryColor = cyanColor;
    let secondaryColor = emeraldColor;

    if (status === 'verified') {
      primaryColor = emeraldColor;
      secondaryColor = cyanColor;
    } else if (status === 'warning') {
      primaryColor = amberColor;
      secondaryColor = alertColor;
    } else if (status === 'contradicted' || status === 'error') {
      primaryColor = alertColor;
      secondaryColor = amberColor;
    } else if (status === 'loading') {
      primaryColor = cyanColor;
      secondaryColor = cyanColor;
    }

    // 2. Anatomical 3D Heart Particle Geometry
    const particleCount = 2600;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    let idx = 0;
    for (let i = 0; i < particleCount; i++) {
      const u = Math.PI * 2 * Math.random();
      const t = Math.PI * (Math.random() * 2 - 1);
      const sinT = Math.sin(t);
      const cosT = Math.cos(t);

      // Coordinate formulation
      let x = 16 * Math.pow(sinT, 3);
      let y = 13 * cosT - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t);
      let z = 16 * Math.pow(sinT, 3) * Math.sin(u) * 0.72;

      // Aorta & superior vessel branches
      const isAorta = i > particleCount - 220;
      if (isAorta) {
        const archT = (i - (particleCount - 220)) / 220;
        const archAngle = archT * Math.PI * 1.15;
        x = Math.sin(archAngle) * 4.2 - 1.8;
        y = 11.5 + Math.cos(archAngle) * 3.8 + (Math.random() - 0.5) * 1.2;
        z = (Math.random() - 0.5) * 3.5;
      } else {
        const depthFactor = 0.78 + Math.random() * 0.32;
        x *= depthFactor;
        y *= depthFactor;
        z *= depthFactor;
      }

      const scale = 0.68;
      positions[idx * 3] = x * scale;
      positions[idx * 3 + 1] = (y - 1.5) * scale;
      positions[idx * 3 + 2] = z * scale;

      const heightRatio = Math.max(0, Math.min(1, (y + 14) / 28));
      const pointColor = new THREE.Color().lerpColors(secondaryColor, primaryColor, heightRatio);

      colors[idx * 3] = pointColor.r;
      colors[idx * 3 + 1] = pointColor.g;
      colors[idx * 3 + 2] = pointColor.b;

      idx++;
    }

    const heartGeometry = new THREE.BufferGeometry();
    heartGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    heartGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // Particle sprite
    const canvasTexture = document.createElement('canvas');
    canvasTexture.width = 32;
    canvasTexture.height = 32;
    const ctx = canvasTexture.getContext('2d');
    if (ctx) {
      const gradient = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
      gradient.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
      gradient.addColorStop(0.3, 'rgba(0, 245, 212, 0.75)');
      gradient.addColorStop(0.7, 'rgba(16, 185, 129, 0.2)');
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 32, 32);
    }
    const particleTexture = new THREE.CanvasTexture(canvasTexture);

    const heartMaterial = new THREE.PointsMaterial({
      size: 0.85,
      map: particleTexture,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const heartPoints = new THREE.Points(heartGeometry, heartMaterial);
    scene.add(heartPoints);

    // 3. Subtle Inner Cage Lattice
    const cageGeometry = new THREE.IcosahedronGeometry(7.2, 2);
    const cageWireframe = new THREE.WireframeGeometry(cageGeometry);
    const cageLineMaterial = new THREE.LineBasicMaterial({
      color: primaryColor,
      transparent: true,
      opacity: 0.14,
      blending: THREE.AdditiveBlending,
    });
    const cageLines = new THREE.LineSegments(cageWireframe, cageLineMaterial);
    cageLines.scale.set(0.85, 1.1, 0.8);
    cageLines.position.set(0, -1, 0);
    scene.add(cageLines);

    // 4. Orbital Telemetry Rings (subtle)
    const createRing = (radius: number, tiltX: number, tiltY: number, color: THREE.Color, speed: number) => {
      const ringGeom = new THREE.RingGeometry(radius - 0.06, radius + 0.06, 64);
      const ringMat = new THREE.MeshBasicMaterial({
        color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.25,
        blending: THREE.AdditiveBlending,
      });
      const ringMesh = new THREE.Mesh(ringGeom, ringMat);
      ringMesh.rotation.x = tiltX;
      ringMesh.rotation.y = tiltY;
      scene.add(ringMesh);
      return { mesh: ringMesh, speed };
    };

    const rings = [
      createRing(13.5, Math.PI / 3, 0.2, cyanColor, 0.004),
      createRing(15.2, -Math.PI / 4, 0.4, primaryColor, -0.003),
    ];

    // Pointer event interaction
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
        rotationRef.current.targetY += deltaX * 0.007;
        rotationRef.current.targetX += deltaY * 0.007;
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
      }
    };

    const handlePointerUp = () => {
      isDragging = false;
    };

    canvas.addEventListener('mousedown', handlePointerDown);
    window.addEventListener('mousemove', handlePointerMove);
    window.addEventListener('mouseup', handlePointerUp);

    // Animation Loop
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Respect reduced motion preference: static scale, no automatic rotation
      let cardiacScale = 1.0;
      if (!prefersReducedMotion) {
        // Subtle resting systolic pulse (70 bpm rhythm = 1.16 Hz)
        const rhythmFreq = status === 'loading' ? 1.5 : 1.16;
        const phase = (elapsedTime * rhythmFreq * Math.PI * 2) % (Math.PI * 2);
        if (phase < Math.PI * 0.35) {
          cardiacScale = 1.0 + Math.sin((phase / (Math.PI * 0.35)) * Math.PI) * 0.045;
        } else if (phase < Math.PI * 0.65) {
          const subPhase = (phase - Math.PI * 0.35) / (Math.PI * 0.3);
          cardiacScale = 1.0 + Math.sin(subPhase * Math.PI) * 0.02;
        }
      }

      // Smooth interpolation for rotation
      const rot = rotationRef.current;
      const baseRotationSpeed = prefersReducedMotion ? 0 : 0.002;
      rot.y += (rot.targetY - rot.y) * 0.06 + baseRotationSpeed;
      rot.x += (rot.targetX - rot.x) * 0.06;

      heartPoints.rotation.y = rot.y;
      heartPoints.rotation.x = rot.x;
      heartPoints.scale.set(cardiacScale, cardiacScale, cardiacScale);

      cageLines.rotation.y = rot.y * 0.85;
      cageLines.rotation.x = rot.x * 0.85;
      cageLines.scale.set(cardiacScale * 0.85, cardiacScale * 1.1, cardiacScale * 0.8);

      if (!prefersReducedMotion) {
        rings.forEach((r) => {
          r.mesh.rotation.z += r.speed;
        });
      }

      renderer.render(scene, camera);
    };

    animate();

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
      renderer.dispose();
    };
  }, [status, webGLSupported, prefersReducedMotion]);

  // Genuine status label mapping (no fabricated BPM or heart metrics)
  const getStatusText = () => {
    switch (status) {
      case 'loading':
        return 'QUERY IN-FLIGHT';
      case 'verified':
        return confidenceLevel ? `GROUNDED (${confidenceLevel})` : 'GROUNDED RESPONSE';
      case 'contradicted':
        return 'CONTRADICTION DETECTED';
      case 'warning':
        return isCorrected ? 'FLAGGED • SELF-CORRECTED' : 'UNGROUNDED CLAIMS';
      case 'error':
        return 'REQUEST FAILED';
      case 'idle':
      default:
        return 'AWAITING QUERY';
    }
  };

  const getTelemetryStatusClass = () => {
    switch (status) {
      case 'loading':
        return 'loading';
      case 'verified':
        return 'verified';
      case 'contradicted':
      case 'error':
        return 'alert';
      case 'warning':
        return 'warning';
      case 'idle':
      default:
        return 'idle';
    }
  };

  return (
    <div
      ref={containerRef}
      className={`holographic-heart-container ${className}`}
      tabIndex={0}
      role="img"
      aria-label={`3D holographic anatomical visualization representing clinical status: ${getStatusText()}. Use arrow keys or mouse drag to rotate.`}
      onKeyDown={handleKeyDown}
      title="3D Holographic Core — Click and drag or use arrow keys to rotate. Press R to reset."
    >
      {webGLSupported ? (
        <canvas ref={canvasRef} className="holographic-heart-canvas" />
      ) : (
        /* Graceful 2D Fallback when WebGL is unavailable */
        <div className="webgl-fallback-container">
          <svg className="fallback-heart-svg" viewBox="0 0 200 200" fill="none" aria-hidden="true">
            <path
              d="M100,165 C60,130 20,95 20,55 C20,30 40,15 65,15 C82,15 95,28 100,38 C105,28 118,15 135,15 C160,15 180,30 180,55 C180,95 140,130 100,165 Z"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeDasharray="4 3"
              className={`fallback-contour ${getTelemetryStatusClass()}`}
            />
            <circle cx="100" cy="90" r="30" stroke="currentColor" strokeWidth="1" opacity="0.3" />
            <line x1="100" y1="40" x2="100" y2="140" stroke="currentColor" strokeWidth="1" opacity="0.3" />
            <line x1="50" y1="90" x2="150" y2="90" stroke="currentColor" strokeWidth="1" opacity="0.3" />
          </svg>
          <span className="fallback-note">2D Telemetry Fallback (WebGL Unavailable)</span>
        </div>
      )}

      {/* Genuine Telemetry Badges */}
      <div className="heart-telemetry-badge top-left">
        <span className="telemetry-label">SYSTEM STATE</span>
        <span className="telemetry-value">
          <span className={`pulse-dot ${getTelemetryStatusClass()}`}></span>
          {getStatusText()}
        </span>
      </div>

      <div className="heart-telemetry-badge top-right">
        <span className="telemetry-label">PIPELINE LATENCY</span>
        <span className={`telemetry-status-pill ${getTelemetryStatusClass()}`}>
          {status === 'loading'
            ? 'IN PROGRESS…'
            : latencyMs !== undefined && latencyMs !== null
            ? `${latencyMs} ms`
            : 'AWAITING QUERY'}
        </span>
      </div>

      <div className="heart-telemetry-badge bottom-center">
        <span className="telemetry-hint">
          {prefersReducedMotion
            ? 'MOTION REDUCED • ARROW KEYS TO ROTATE'
            : isInteracting
            ? 'INTERACTIVE ROTATION ACTIVE'
            : 'DRAG OR USE ARROW KEYS TO ROTATE'}
        </span>
      </div>
    </div>
  );
};
