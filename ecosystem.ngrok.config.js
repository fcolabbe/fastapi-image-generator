module.exports = {
  apps: [{
    name: 'ngrok-tunnel',
    script: 'ngrok',
    args: 'http 8000 --log=stdout',
    cwd: '/var/www/fastapi-image-generator',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    },
    error_file: '/var/log/pm2/ngrok-error.log',
    out_file: '/var/log/pm2/ngrok-out.log',
    log_file: '/var/log/pm2/ngrok-combined.log',
    time: true
  }]
}

