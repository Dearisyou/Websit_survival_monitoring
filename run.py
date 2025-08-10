from app import create_app, db, scheduler
from app.models import Website
from app.monitor import add_monitor_job

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # 启动所有监控任务
        websites = Website.query.all()
        for website in websites:
            add_monitor_job(website.id)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()