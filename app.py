<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Neon Zombie Survival</title>
    <style>
        body {
            margin: 0;
            overflow: hidden;
            background: #050505;
            font-family: 'Courier New', Courier, monospace;
            touch-action: none; /* Prevent pull-to-refresh on mobile */
        }
        canvas {
            display: block;
        }
        #ui-layer {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            display: flex;
            flex-direction: column;
            justify_content: space-between;
        }
        #hud {
            padding: 20px;
            display: flex;
            justify-content: space-between;
            color: #0ff;
            font-size: 20px;
            font-weight: bold;
            text-shadow: 0 0 10px #0ff;
        }
        #health-bar-container {
            width: 200px;
            height: 20px;
            border: 2px solid #0ff;
            border-radius: 10px;
            overflow: hidden;
        }
        #health-fill {
            width: 100%;
            height: 100%;
            background: #0ff;
            transition: width 0.2s;
        }
        .screen {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            pointer-events: auto;
            backdrop-filter: blur(5px);
            z-index: 10;
        }
        h1 {
            color: #f0f;
            font-size: 48px;
            margin-bottom: 10px;
            text-shadow: 0 0 20px #f0f;
            text-align: center;
        }
        p {
            color: #fff;
            margin-bottom: 30px;
            text-align: center;
            line-height: 1.5;
        }
        button {
            background: transparent;
            color: #0ff;
            border: 2px solid #0ff;
            padding: 15px 40px;
            font-size: 24px;
            font-family: inherit;
            cursor: pointer;
            text-transform: uppercase;
            box-shadow: 0 0 15px #0ff;
            transition: all 0.2s;
        }
        button:hover {
            background: #0ff;
            color: #000;
        }
        .hidden {
            display: none !important;
        }
        /* Mobile Joystick Hints */
        .touch-zone {
            position: absolute;
            bottom: 20px;
            width: 150px;
            height: 150px;
            border: 2px dashed rgba(255,255,255,0.2);
            border-radius: 50%;
            pointer-events: none;
            display: none; /* Shown via JS on touch */
        }
        #zone-left { left: 20px; }
        #zone-left::after { content: 'MOVE'; position:absolute; top: 50%; left:50%; transform:translate(-50%, -50%); color:rgba(255,255,255,0.3); }
        #zone-right { right: 20px; border-color: rgba(255, 0, 0, 0.2); }
        #zone-right::after { content: 'AIM/SHOOT'; position:absolute; top: 50%; left:50%; transform:translate(-50%, -50%); color:rgba(255,0,0,0.3); }

        @media (max-width: 768px) {
            .touch-zone { display: block; }
        }
    </style>
</head>
<body>

    <canvas id="gameCanvas"></canvas>

    <div id="ui-layer">
        <div id="hud">
            <div>SCORE: <span id="score">0</span></div>
            <div id="health-bar-container"><div id="health-fill"></div></div>
        </div>
        
        <!-- Mobile Controls Overlay -->
        <div id="zone-left" class="touch-zone"></div>
        <div id="zone-right" class="touch-zone"></div>
    </div>

    <!-- Start Screen -->
    <div id="start-screen" class="screen">
        <h1>NEON DEAD</h1>
        <p>Desktop: WASD to Move, Mouse to Shoot<br>Mobile: Left Touch to Move, Right Touch to Shoot</p>
        <button onclick="startGame()">Start Mission</button>
    </div>

    <!-- Game Over Screen -->
    <div id="game-over-screen" class="screen hidden">
        <h1 style="color: #f00; text-shadow: 0 0 20px #f00;">WASTED</h1>
        <p>Final Score: <span id="final-score">0</span></p>
        <button onclick="resetGame()">Try Again</button>
    </div>

    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        
        // Game State
        let gameRunning = false;
        let score = 0;
        let animationId;
        let frameCount = 0;
        let lastTime = 0;
        
        // Entities
        let player;
        let bullets = [];
        let zombies = [];
        let particles = [];

        // Inputs
        const keys = { w: false, a: false, s: false, d: false };
        const mouse = { x: 0, y: 0, down: false };
        const touchInput = { 
            active: false, 
            moveX: 0, 
            moveY: 0, 
            shootX: 0, 
            shootY: 0,
            shooting: false 
        };

        // Resize
        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resize);
        resize();

        // --- Classes ---

        class Player {
            constructor() {
                this.reset();
            }
            
            reset() {
                this.x = canvas.width / 2;
                this.y = canvas.height / 2;
                this.radius = 15;
                this.color = '#0ff';
                this.speed = 4;
                this.hp = 100;
                this.maxHp = 100;
                this.angle = 0;
                this.lastShot = 0;
                this.fireRate = 150; // ms
            }

            draw() {
                ctx.save();
                ctx.translate(this.x, this.y);
                ctx.rotate(this.angle);

                // Gun
                ctx.fillStyle = '#0aa';
                ctx.fillRect(0, -5, 35, 10);

                // Body
                ctx.beginPath();
                ctx.arc(0, 0, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.shadowBlur = 15;
                ctx.shadowColor = this.color;
                ctx.fill();
                ctx.closePath();

                ctx.restore();
            }

            update(dt) {
                // Movement
                let dx = 0;
                let dy = 0;

                if (touchInput.active) {
                    dx = touchInput.moveX * this.speed;
                    dy = touchInput.moveY * this.speed;
                } else {
                    if (keys.w) dy -= this.speed;
                    if (keys.s) dy += this.speed;
                    if (keys.a) dx -= this.speed;
                    if (keys.d) dx += this.speed;
                }

                this.x += dx;
                this.y += dy;

                // Boundaries
                this.x = Math.max(this.radius, Math.min(canvas.width - this.radius, this.x));
                this.y = Math.max(this.radius, Math.min(canvas.height - this.radius, this.y));

                // Aiming
                if (touchInput.active && (touchInput.shootX !== 0 || touchInput.shootY !== 0)) {
                    this.angle = Math.atan2(touchInput.shootY, touchInput.shootX);
                } else if (!touchInput.active) {
                    this.angle = Math.atan2(mouse.y - this.y, mouse.x - this.x);
                }

                // Shooting
                const now = Date.now();
                if ((mouse.down || touchInput.shooting) && now - this.lastShot > this.fireRate) {
                    this.shoot();
                    this.lastShot = now;
                }
            }

            shoot() {
                const muzzleDist = 35;
                const bx = this.x + Math.cos(this.angle) * muzzleDist;
                const by = this.y + Math.sin(this.angle) * muzzleDist;
                
                bullets.push(new Bullet(bx, by, this.angle));
                
                // Recoil effect
                this.x -= Math.cos(this.angle) * 2;
                this.y -= Math.sin(this.angle) * 2;
            }
        }

        class Bullet {
            constructor(x, y, angle) {
                this.x = x;
                this.y = y;
                this.vx = Math.cos(angle) * 12;
                this.vy = Math.sin(angle) * 12;
                this.radius = 3;
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = '#ff0';
                ctx.shadowBlur = 10;
                ctx.shadowColor = '#ff0';
                ctx.fill();
            }

            update() {
                this.x += this.vx;
                this.y += this.vy;
            }
        }

        class Zombie {
            constructor() {
                // Spawn at random edge
                if (Math.random() < 0.5) {
                    this.x = Math.random() < 0.5 ? -20 : canvas.width + 20;
                    this.y = Math.random() * canvas.height;
                } else {
                    this.x = Math.random() * canvas.width;
                    this.y = Math.random() < 0.5 ? -20 : canvas.height + 20;
                }

                this.speed = 1 + Math.random() * 1.5 + (score / 500); // Get faster over time
                this.radius = 16;
                this.color = '#f0f';
                this.hp = 1 + Math.floor(score / 300); // Get tougher over time
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.shadowBlur = 10;
                ctx.shadowColor = this.color;
                ctx.fill();
                
                // Eyes
                const angle = Math.atan2(player.y - this.y, player.x - this.x);
                ctx.fillStyle = '#fff';
                ctx.beginPath();
                ctx.arc(this.x + Math.cos(angle - 0.5) * 8, this.y + Math.sin(angle - 0.5) * 8, 3, 0, Math.PI*2);
                ctx.arc(this.x + Math.cos(angle + 0.5) * 8, this.y + Math.sin(angle + 0.5) * 8, 3, 0, Math.PI*2);
                ctx.fill();
            }

            update() {
                const angle = Math.atan2(player.y - this.y, player.x - this.x);
                this.x += Math.cos(angle) * this.speed;
                this.y += Math.sin(angle) * this.speed;
            }
        }

        class Particle {
            constructor(x, y, color) {
                this.x = x;
                this.y = y;
                const angle = Math.random() * Math.PI * 2;
                const speed = Math.random() * 3;
                this.vx = Math.cos(angle) * speed;
                this.vy = Math.sin(angle) * speed;
                this.alpha = 1;
                this.color = color;
                this.size = Math.random() * 3 + 1;
            }

            draw() {
                ctx.save();
                ctx.translate(this.x, this.y);
                const angle = Math.atan2(player.y - this.y, player.x - this.x);
                ctx.rotate(angle);

                // Arms
                ctx.fillStyle = '#2a442a'; // Dark green for arms
                ctx.beginPath();
                ctx.moveTo(5, 5);
                ctx.lineTo(20, 10);
                ctx.lineTo(20, -10);
                ctx.lineTo(5, -5);
                ctx.fill();

                // Body
                ctx.beginPath();
                ctx.arc(0, 0, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = '#3a5a3a'; // Main zombie color (dark green)
                ctx.shadowBlur = 15;
                ctx.shadowColor = '#1a3a1a';
                ctx.fill();

                // "T-shirt" / Rags
                ctx.beginPath();
                ctx.arc(0, 0, this.radius * 0.8, -Math.PI / 2, Math.PI / 2);
                ctx.fillStyle = '#4a6a4a'; // Slightly lighter green for rags
                ctx.fill();

                // Eyes
                ctx.fillStyle = '#800'; // Dark red for eye sockets
                ctx.beginPath();
                ctx.arc(8, -4, 4, 0, Math.PI*2);
                ctx.arc(8, 4, 4, 0, Math.PI*2);
                ctx.fill();

                ctx.fillStyle = '#ff0'; // Yellow pupils
                ctx.beginPath();
                ctx.arc(9, -4, 1.5, 0, Math.PI*2);
                ctx.arc(9, 4, 1.5, 0, Math.PI*2);
                ctx.fill();

                // "Grime" particles
                ctx.fillStyle = '#1a2a1a';
                for (let i = 0; i < 3; i++) {
                    const pAngle = Math.random() * Math.PI * 2;
                    const pDist = Math.random() * this.radius;
                    ctx.beginPath();
                    ctx.arc(Math.cos(pAngle) * pDist, Math.sin(pAngle) * pDist, 1.5, 0, Math.PI*2);
                    ctx.fill();
                }

                ctx.restore();
            }

            update() {
                this.x += this.vx;
                this.y += this.vy;
                this.alpha -= 0.03;
            }
        }

        // --- Core Logic ---

        function init() {
            player = new Player();
            bullets = [];
            zombies = [];
            particles = [];
            score = 0;
            updateUI();
        }

        function spawnZombie() {
            // Spawn rate increases with score
            const spawnChance = 0.02 + (score / 5000); 
            if (Math.random() < spawnChance) {
                zombies.push(new Zombie());
            }
        }

        function createExplosion(x, y, color, count) {
            for (let i = 0; i < count; i++) {
                particles.push(new Particle(x, y, color));
            }
        }

        function checkCollisions() {
            // Bullet vs Zombie
            for (let i = bullets.length - 1; i >= 0; i--) {
                for (let j = zombies.length - 1; j >= 0; j--) {
                    const b = bullets[i];
                    const z = zombies[j];
                    if (!b || !z) continue;

                    const dist = Math.hypot(b.x - z.x, b.y - z.y);
                    
                    if (dist < z.radius + b.radius) {
                        // Hit
                        z.hp--;
                        bullets.splice(i, 1); // Remove bullet
                        createExplosion(z.x, z.y, '#f0f', 3); // Blood splatter
                        
                        if (z.hp <= 0) {
                            zombies.splice(j, 1);
                            score += 10;
                            createExplosion(z.x, z.y, '#f0f', 15); // Big explosion
                            updateUI();
                        }
                        break; // Bullet hit something, stop checking this bullet
                    }
                }
            }

            // Zombie vs Player
            for (let i = 0; i < zombies.length; i++) {
                const z = zombies[i];
                const dist = Math.hypot(z.x - player.x, z.y - player.y);
                
                if (dist < z.radius + player.radius) {
                    player.hp -= 1;
                    updateUI();
                    createExplosion(player.x, player.y, '#f00', 1); // Player bleed
                    
                    // Push zombie back slightly
                    const angle = Math.atan2(z.y - player.y, z.x - player.x);
                    z.x += Math.cos(angle) * 5;
                    z.y += Math.sin(angle) * 5;

                    if (player.hp <= 0) {
                        gameOver();
                    }
                }
            }
        }

        function updateUI() {
            document.getElementById('score').innerText = score;
            const healthPct = Math.max(0, (player.hp / player.maxHp) * 100);
            document.getElementById('health-fill').style.width = healthPct + '%';
            
            if (healthPct < 30) {
                document.getElementById('health-fill').style.backgroundColor = '#f00';
            } else {
                document.getElementById('health-fill').style.backgroundColor = '#0ff';
            }
        }

        function drawGrid() {
            ctx.strokeStyle = 'rgba(20, 20, 30, 0.5)';
            ctx.lineWidth = 1;
            const size = 50;
            const offsetX = -player.x % size;
            const offsetY = -player.y % size;
            
            // To make it look like we are moving, we actually move the world, 
            // but for this simple version, player moves. 
            // Let's just draw a static grid for reference.
            for (let x = 0; x < canvas.width; x += size) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
            }
            for (let y = 0; y < canvas.height; y += size) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
            }
        }

        function loop() {
            if (!gameRunning) return;

            // Clear
            ctx.fillStyle = '#050505';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            drawGrid();

            // Update & Draw Player
            player.update();
            player.draw();

            // Update & Draw Bullets
            for (let i = bullets.length - 1; i >= 0; i--) {
                bullets[i].update();
                bullets[i].draw();
                // Remove if off screen
                if (bullets[i].x < 0 || bullets[i].x > canvas.width || 
                    bullets[i].y < 0 || bullets[i].y > canvas.height) {
                    bullets.splice(i, 1);
                }
            }

            // Spawner
            spawnZombie();

            // Update & Draw Zombies
            for (let i = 0; i < zombies.length; i++) {
                zombies[i].update();
                zombies[i].draw();
            }

            // Update & Draw Particles
            for (let i = particles.length - 1; i >= 0; i--) {
                particles[i].update();
                particles[i].draw();
                if (particles[i].alpha <= 0) particles.splice(i, 1);
            }

            checkCollisions();

            animationId = requestAnimationFrame(loop);
        }

        function startGame() {
            document.getElementById('start-screen').classList.add('hidden');
            document.getElementById('game-over-screen').classList.add('hidden');
            gameRunning = true;
            init();
            loop();
        }

        function gameOver() {
            gameRunning = false;
            cancelAnimationFrame(animationId);
            document.getElementById('final-score').innerText = score;
            document.getElementById('game-over-screen').classList.remove('hidden');
        }

        function resetGame() {
            startGame();
        }

        // --- Input Listeners ---

        window.addEventListener('keydown', e => {
            if (e.key === 'w' || e.key === 'ArrowUp') keys.w = true;
            if (e.key === 'a' || e.key === 'ArrowLeft') keys.a = true;
            if (e.key === 's' || e.key === 'ArrowDown') keys.s = true;
            if (e.key === 'd' || e.key === 'ArrowRight') keys.d = true;
        });

        window.addEventListener('keyup', e => {
            if (e.key === 'w' || e.key === 'ArrowUp') keys.w = false;
            if (e.key === 'a' || e.key === 'ArrowLeft') keys.a = false;
            if (e.key === 's' || e.key === 'ArrowDown') keys.s = false;
            if (e.key === 'd' || e.key === 'ArrowRight') keys.d = false;
        });

        window.addEventListener('mousemove', e => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });

        window.addEventListener('mousedown', () => mouse.down = true);
        window.addEventListener('mouseup', () => mouse.down = false);

        // Touch Logic (Virtual Joystick & Shooting)
        window.addEventListener('touchstart', handleTouch, {passive: false});
        window.addEventListener('touchmove', handleTouch, {passive: false});
        window.addEventListener('touchend', endTouch);

        function handleTouch(e) {
            e.preventDefault();
            touchInput.active = true;
            
            // Reset states for multitouch handling
            let moveTouch = null;
            let shootTouch = null;

            for (let i = 0; i < e.touches.length; i++) {
                const t = e.touches[i];
                if (t.clientX < window.innerWidth / 2) {
                    moveTouch = t;
                } else {
                    shootTouch = t;
                }
            }

            // Movement Logic (Left side)
            if (moveTouch) {
                // Calculate vector from center of left zone (approx)
                // Or simpler: just treat center of screen as origin for movement
                // Let's do a virtual joystick relative to initial touch would be better, 
                // but for simplicity: relative to center of left half
                const centerX = window.innerWidth / 4;
                const centerY = window.innerHeight - 100; // approximate thumb position
                
                const dx = moveTouch.clientX - centerX;
                const dy = moveTouch.clientY - centerY;
                const dist = Math.hypot(dx, dy);
                const maxDist = 1; // Normalize
                
                touchInput.moveX = dx / dist || 0;
                touchInput.moveY = dy / dist || 0;
            } else {
                touchInput.moveX = 0;
                touchInput.moveY = 0;
            }

            // Shooting Logic (Right side)
            if (shootTouch) {
                touchInput.shooting = true;
                const centerX = (window.innerWidth / 4) * 3;
                const centerY = window.innerHeight - 100;
                touchInput.shootX = shootTouch.clientX - centerX;
                touchInput.shootY = shootTouch.clientY - centerY;
            } else {
                touchInput.shooting = false;
            }
        }

        function endTouch(e) {
            if (e.touches.length === 0) {
                touchInput.active = false;
                touchInput.moveX = 0;
                touchInput.moveY = 0;
                touchInput.shooting = false;
            } else {
                handleTouch(e); // Re-evaluate remaining touches
            }
        }

    </script>
</body>
</html>
