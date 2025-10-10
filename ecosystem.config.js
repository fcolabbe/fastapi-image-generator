module.exports = {
  apps: [{
    name: 'fastapi-image-generator',
    script: 'app.py',
    interpreter: '/var/www/fastapi-image-generator/venv/bin/python',
    cwd: '/var/www/fastapi-image-generator',
    instances: 1,
    exec_mode: 'fork',
    env: {
      NODE_ENV: 'production',
      PYTHONPATH: '/var/www/fastapi-image-generator',
      PYTHONUNBUFFERED: '1'
    },
    error_file: '/var/log/pm2/fastapi-image-generator-error.log',
    out_file: '/var/log/pm2/fastapi-image-generator-out.log',
    log_file: '/var/log/pm2/fastapi-image-generator.log',
    time: true,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    restart_delay: 4000,
    max_restarts: 10,
    min_uptime: '10s'
  }]
};
