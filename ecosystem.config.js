module.exports = {
  apps: [
    {
      name: 'ai-orchestrator',
      script: './orchestrator.py',
      interpreter: 'python3',
      watch: false,
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      error_file: './logs/orchestrator_error.log',
      out_file: './logs/orchestrator_out.log',
      log_file: './logs/orchestrator_combined.log',
      time: true,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '.'
      }
    },
    {
      name: 'gmail-watcher',
      script: './watcher_runner.py',
      interpreter: 'python3',
      args: 'gmail',
      watch: false,
      instances: 1,
      autorestart: true,
      max_restarts: 5,
      restart_delay: 10000,
      error_file: './logs/gmail_watcher_error.log',
      out_file: './logs/gmail_watcher_out.log',
      log_file: './logs/gmail_watcher_combined.log',
      time: true,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '.'
      }
    },
    {
      name: 'whatsapp-watcher',
      script: './watcher_runner.py',
      interpreter: 'python3',
      args: 'whatsapp',
      watch: false,
      instances: 1,
      autorestart: true,
      max_restarts: 5,
      restart_delay: 10000,
      error_file: './logs/whatsapp_watcher_error.log',
      out_file: './logs/whatsapp_watcher_out.log',
      log_file: './logs/whatsapp_watcher_combined.log',
      time: true,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '.'
      }
    },
    {
      name: 'linkedin-watcher',
      script: './watcher_runner.py',
      interpreter: 'python3',
      args: 'linkedin',
      watch: false,
      instances: 1,
      autorestart: true,
      max_restarts: 5,
      restart_delay: 10000,
      error_file: './logs/linkedin_watcher_error.log',
      out_file: './logs/linkedin_watcher_out.log',
      log_file: './logs/linkedin_watcher_combined.log',
      time: true,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '.'
      }
    }
  ]
};