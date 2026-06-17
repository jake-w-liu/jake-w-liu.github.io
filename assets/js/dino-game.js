
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('dino-game');
    const ctx = canvas.getContext('2d');
    canvas.width = 600;
    canvas.height = 150;

    let score = 0;
    let highScore = 0;
    let isGameOver = false;

    const dino = {
        x: 50,
        y: 100,
        width: 20,
        height: 20,
        color: '#333',
        velocityY: 0,
        isJumping: false,
        draw() {
            ctx.fillStyle = this.color;
            ctx.fillRect(this.x, this.y, this.width, this.height);
        }
    };

    const obstacles = [];
    let frameCount = 0;

    function addObstacle() {
        const obstacle = {
            x: canvas.width,
            y: 100,
            width: 10,
            height: 20,
            color: 'red',
            speed: 2,
            draw() {
                ctx.fillStyle = this.color;
                ctx.fillRect(this.x, this.y, this.width, this.height);
            }
        };
        obstacles.push(obstacle);
    }

    function update() {
        if (isGameOver) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Dino
        dino.draw();
        if (dino.isJumping) {
            dino.y += dino.velocityY;
            dino.velocityY += 0.5; // Gravity
            if (dino.y >= 100) {
                dino.y = 100;
                dino.isJumping = false;
            }
        }

        // Obstacles
        frameCount++;
        if (frameCount % 120 === 0) {
            addObstacle();
        }

        for (let i = obstacles.length - 1; i >= 0; i--) {
            const obstacle = obstacles[i];
            obstacle.x -= obstacle.speed;
            obstacle.draw();

            // Collision detection
            if (
                dino.x < obstacle.x + obstacle.width &&
                dino.x + dino.width > obstacle.x &&
                dino.y < obstacle.y + obstacle.height &&
                dino.y + dino.height > obstacle.y
            ) {
                isGameOver = true;
                if (score > highScore) {
                    highScore = score;
                }
            }

            if (obstacle.x + obstacle.width < 0) {
                obstacles.splice(i, 1);
                score++;
            }
        }

        // Score
        ctx.fillStyle = '#333';
        ctx.font = '16px Arial';
        ctx.fillText(`Score: ${score}`, 10, 20);
        ctx.fillText(`High Score: ${highScore}`, 10, 40);


        if (isGameOver) {
            ctx.fillStyle = '#333';
            ctx.font = '24px Arial';
            ctx.fillText('Game Over', canvas.width / 2 - 60, canvas.height / 2);
            ctx.font = '16px Arial';
            ctx.fillText('Press Space to Restart', canvas.width / 2 - 75, canvas.height / 2 + 20);
        }

        requestAnimationFrame(update);
    }

    function jump() {
        if (!dino.isJumping) {
            dino.isJumping = true;
            dino.velocityY = -10;
        }
    }

    function restart() {
        isGameOver = false;
        score = 0;
        obstacles.length = 0;
        dino.y = 100;
        frameCount = 0;
        update();
    }

    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space') {
            if (isGameOver) {
                restart();
            } else {
                jump();
            }
        }
    });

    update();
});
