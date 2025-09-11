import getpass
import json
import logging
import click
from flask.cli import with_appcontext
from backend.app import app, db
from backend.models.user import User
from backend.models.disciplina import Disciplina

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    pass

@click.command("create-admin")
@with_appcontext
def create_admin():
    """Creates the admin user."""
    try:
        admin_user = db.session.execute(db.select(User).filter_by(id_func='ADMIN')).scalar_one_or_none()
        if admin_user:
            logger.info("Admin user already exists.")
            return

        logger.info("Creating admin user...")
        password = getpass.getpass("Enter password for admin user: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if password != confirm_password:
            logger.error("Passwords do not match.")
            return

        new_admin = User(
            id_func='ADMIN',
            username='admin',
            email='admin@escola.com.br',
            role='admin',
            is_active=True
        )
        new_admin.set_password(password)

        db.session.add(new_admin)
        db.session.commit()
        logger.info("Admin user created successfully!")

    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.session.rollback()

@click.command("create-programmer")
@with_appcontext
def create_programmer():
    """Creates the programmer user."""
    try:
        prog_user = db.session.execute(db.select(User).filter_by(id_func='PROG001')).scalar_one_or_none()
        if prog_user:
            logger.info("Programmer user already exists.")
            return

        logger.info("Creating programmer user...")
        password = getpass.getpass("Enter password for programmer user: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if password != confirm_password:
            logger.error("Passwords do not match.")
            return

        new_programmer = User(
            id_func='PROG001',
            username='programador',
            email='dev@escola.com.br',
            role='programador',
            is_active=True
        )
        new_programmer.set_password(password)

        db.session.add(new_programmer)
        db.session.commit()
        logger.info("Programmer user created successfully!")

    except Exception as e:
        logger.error(f"Error creating programmer user: {e}")
        db.session.rollback()

@click.command("seed-disciplinas")
@with_appcontext
def seed_disciplinas():
    """Seeds the database with a default list of disciplinas."""
    try:
        with open('disciplinas.json', 'r', encoding='utf-8') as f:
            lista_disciplinas = json.load(f)

        logger.info("Verifying and adding disciplinas...")
        count = 0
        for nome_materia in lista_disciplinas:
            disciplina_existe = db.session.execute(db.select(Disciplina).filter_by(materia=nome_materia)).scalar_one_or_none()
            if not disciplina_existe:
                nova_disciplina = Disciplina(materia=nome_materia, carga_horaria_prevista=0)
                db.session.add(nova_disciplina)
                count += 1
        
        if count > 0:
            db.session.commit()
            logger.info(f"{count} new disciplina(s) added successfully!")
        else:
            logger.info("All default disciplinas already exist in the database.")

    except FileNotFoundError:
        logger.error("The file 'disciplinas.json' was not found.")
    except Exception as e:
        logger.error(f"Error seeding disciplinas: {e}")
        db.session.rollback()

cli.add_command(create_admin)
cli.add_command(create_programmer)
cli.add_command(seed_disciplinas)

if __name__ == '__main__':
    cli()