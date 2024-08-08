import asqlite
from datetime import datetime, timedelta
import random

async def add_job(job_id: str, job_name: str, job_description: str, job_pay: int, acceptance_chance: float):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''INSERT OR REPLACE INTO jobs (job_id, job_name, job_description, job_pay, acceptance_chance)
                                    VALUES (?, ?, ?, ?, ?)''',
                                 (job_id, job_name, job_description, job_pay, acceptance_chance))
        await conn.commit()


async def get_jobs():
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT job_id, job_name, job_description, job_pay, acceptance_chance FROM jobs')
            jobs = await cursor.fetchall()
    return jobs

async def apply_for_job(user_id: int, job_id: str):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            # Check if user already has a job
            await cursor.execute('SELECT job_id FROM user_jobs WHERE user_id = ?', (user_id,))
            current_job = await cursor.fetchone()
            if current_job:
                return False, "You already have a job. Resign before applying for a new one."

            # Check cooldown
            now = datetime.utcnow()
            await cursor.execute('SELECT application_time FROM job_applications WHERE user_id = ? AND job_id = ?', (user_id, job_id))
            result = await cursor.fetchone()
            if result:
                last_application_time = datetime.fromisoformat(result[0])
                if now - last_application_time < timedelta(hours=1):
                    remaining_time = timedelta(hours=1) - (now - last_application_time)
                    return False, f"You need to wait **{str(remaining_time).split('.')[0]}** before applying for this job again."

            # Log the application attempt
            await cursor.execute('INSERT INTO job_applications (user_id, job_id, application_time) VALUES (?, ?, ?)',
                                 (user_id, job_id, now.isoformat()))

            # Get the job's acceptance chance
            await cursor.execute('SELECT acceptance_chance FROM jobs WHERE job_id = ?', (job_id,))
            job = await cursor.fetchone()
            if not job:
                return False, "Job not found."

            acceptance_chance = job[0]
            if random.random() <= acceptance_chance:
                await cursor.execute('INSERT INTO user_jobs (user_id, job_id, start_time) VALUES (?, ?, ?)',
                                     (user_id, job_id, now.isoformat()))
                await conn.commit()
                return True, "Congratulations! You've been accepted for the job."
            else:
                await conn.commit()
                return False, "Unfortunately, you were not accepted for the job."



async def resign_from_job(user_id: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT start_time FROM user_jobs WHERE user_id = ?', (user_id,))
            job = await cursor.fetchone()
            if not job:
                return False, "You don't have a job to resign from."

            start_time = datetime.fromisoformat(job[0])
            now = datetime.utcnow()
            if now - start_time < timedelta(hours=2):
                return False, "You can only resign 2 hours after applying for the job."

            await cursor.execute('DELETE FROM user_jobs WHERE user_id = ?', (user_id,))
            await conn.commit()
            return True, "You have successfully resigned from your job."

async def get_user_job(user_id: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''SELECT jobs.job_name, jobs.job_description, jobs.job_pay
                                   FROM user_jobs
                                   JOIN jobs ON user_jobs.job_id = jobs.job_id
                                   WHERE user_jobs.user_id = ?''', (user_id,))
            job = await cursor.fetchone()
    return job


async def get_last_work_time(user_id):
    """Fetch the last work time from the database."""
    async with asqlite.connect('space.db') as db:
        cursor = await db.execute('SELECT last_work_time FROM user_jobs WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        return datetime.fromisoformat(result[0]) if result and result[0] else None

async def update_last_work_time(user_id):
    """Update the last work time in the database."""
    now = datetime.utcnow().isoformat()
    async with asqlite.connect('space.db') as db:
        await db.execute('UPDATE user_jobs SET last_work_time = ? WHERE user_id = ?', (now, user_id))
        await db.commit()


async def update_job_points(user_id: int):
    """Update job points for the user with a random amount."""
    job_points = random.randint(100, 1000)  # Adjust range as needed
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                UPDATE users
                SET job_points = job_points + ?
                WHERE user_id = ?
            ''', (job_points, user_id))
        await conn.commit()
    return job_points