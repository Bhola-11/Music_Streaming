/**
 * MusicVerse 3D Background Engine
 * Renders an interactive 3D cosmic particle wave & constellation using Three.js / WebGL.
 * Reacts dynamically to mouse movement, scroll, and audio visualizer frequency spectrum.
 */

class Cosmic3DBackground {
  constructor() {
    this.canvas = document.getElementById('webgl-background-canvas');
    if (!this.canvas) return;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.particles = null;
    this.particleCount = 1800;
    this.geometry = null;
    this.material = null;
    this.mouseX = 0;
    this.mouseY = 0;
    this.targetMouseX = 0;
    this.targetMouseY = 0;
    this.audioFrequencyBoost = 1.0;
    this.clock = null;

    this.init();
  }

  init() {
    if (typeof THREE === 'undefined') {
      console.warn('Three.js not loaded. Falling back to 2D Canvas Starfield.');
      this.init2DFallback();
      return;
    }

    // 1. Scene & Clock
    this.scene = new THREE.Scene();
    this.clock = new THREE.Clock();

    // 2. Camera
    this.camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      1,
      1000
    );
    this.camera.position.z = 400;

    // 3. WebGL Renderer
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      alpha: true,
      antialias: true,
    });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // 4. Particle Constellation Geometry
    this.geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(this.particleCount * 3);
    const colors = new Float32Array(this.particleCount * 3);

    const cyan = new THREE.Color(0x00f5d4);
    const purple = new THREE.Color(0x7b2cbf);
    const pink = new THREE.Color(0xf72585);
    const baseColor = new THREE.Color();

    for (let i = 0; i < this.particleCount * 3; i += 3) {
      // Cylindrical/spherical cosmic distribution
      positions[i] = (Math.random() - 0.5) * 1200;
      positions[i + 1] = (Math.random() - 0.5) * 800;
      positions[i + 2] = (Math.random() - 0.5) * 1000;

      const mixRatio = Math.random();
      if (mixRatio < 0.45) {
        baseColor.copy(cyan);
      } else if (mixRatio < 0.8) {
        baseColor.copy(purple);
      } else {
        baseColor.copy(pink);
      }

      colors[i] = baseColor.r;
      colors[i + 1] = baseColor.g;
      colors[i + 2] = baseColor.b;
    }

    this.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    this.geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // 5. Shader/Points Material
    this.material = new THREE.PointsMaterial({
      size: 3.5,
      vertexColors: true,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending,
    });

    this.particles = new THREE.Points(this.geometry, this.material);
    this.scene.add(this.particles);

    // 6. Event Listeners
    window.addEventListener('resize', this.onWindowResize.bind(this));
    window.addEventListener('mousemove', this.onMouseMove.bind(this));

    // 7. Start Render Loop
    this.animate();
  }

  onMouseMove(e) {
    this.targetMouseX = (e.clientX - window.innerWidth / 2) * 0.15;
    this.targetMouseY = (e.clientY - window.innerHeight / 2) * 0.15;
  }

  onWindowResize() {
    if (!this.camera || !this.renderer) return;
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  setAudioFrequencyBoost(boost) {
    this.audioFrequencyBoost = Math.max(1.0, boost);
  }

  animate() {
    requestAnimationFrame(this.animate.bind(this));

    const elapsedTime = this.clock.getElapsedTime();

    // Smooth camera mouse follow
    this.mouseX += (this.targetMouseX - this.mouseX) * 0.05;
    this.mouseY += (this.targetMouseY - this.mouseY) * 0.05;

    this.camera.position.x = this.mouseX;
    this.camera.position.y = -this.mouseY;
    this.camera.lookAt(this.scene.position);

    // Rotate particles with subtle organic flow
    if (this.particles) {
      this.particles.rotation.y = elapsedTime * 0.03;
      this.particles.rotation.x = Math.sin(elapsedTime * 0.02) * 0.1;

      // Pulse size with audio energy
      this.material.size = 3.5 * this.audioFrequencyBoost;
    }

    this.renderer.render(this.scene, this.camera);
  }

  init2DFallback() {
    const ctx = this.canvas.getContext('2d');
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;

    const stars = Array.from({ length: 150 }, () => ({
      x: Math.random() * this.canvas.width,
      y: Math.random() * this.canvas.height,
      radius: Math.random() * 1.5,
      alpha: Math.random(),
      speed: Math.random() * 0.5 + 0.1,
    }));

    const render = () => {
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      ctx.fillStyle = '#0a0b10';
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

      stars.forEach((star) => {
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 245, 212, ${star.alpha})`;
        ctx.fill();

        star.y -= star.speed;
        if (star.y < 0) star.y = this.canvas.height;
      });

      requestAnimationFrame(render);
    };
    render();
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.musicverse3D = new Cosmic3DBackground();
});
