from app import create_app, db
import sqlalchemy as sa
import sqlalchemy.orm as saorm
from app.models import User, Post

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'saorm': saorm, 'db': db, 'User': User, 'Post': Post}

if __name__ == '__main__':
    app.run(debug=True)
