from csv import DictWriter
import os
from shutil import copy
import zipfile

SAVE_PATH = "data/saves/"
TEMPORARY = "data/temporary"
TEMPLATES = "resources/templates/"


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file),
                       os.path.relpath(os.path.join(root, file),
                                       os.path.join(path, '.')))


def autosave(session):
    if session.measurement_name is None:
        return

    dir_name = f"{session.measurement_name}"
    dir_path = os.path.join(SAVE_PATH, dir_name)
    try:
        os.mkdir(dir_path)
    except FileExistsError:
        pass

    file_name = f"day_{session.day}_hour_{session.hour}.zip"
    file_path = os.path.join(dir_path, file_name)
    save_session(session, file_path)


def save_session(session, path):
    try:
        with open(os.path.join(TEMPORARY, "data.csv"), 'w') as file:
            # TODO: Change these fieldnames
            fieldnames = ['time', 'measurement', 'set_temp']
            writer = DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for time, real, target in zip(session.times, session.real_temps, session.target_temps):
                writer.writerow(
                    {'time': time, 'measurement': real, 'set_temp': target}
                )
    except Exception:
        return "Could not open temporary files used for saving."
    # TODO: Clean up/Remove files that you created for export

    src = os.path.join(TEMPLATES, "profile.csv")
    dest = os.path.join(TEMPORARY, "profile.csv")
    copy(src, dest)

    upper_limit = 100
    for i in range(upper_limit):
        current_path = path.join(f"_v{i}")
        try:
            with zipfile.ZipFile(current_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipdir(TEMPORARY, zipf)
        except Exception:
            continue
        finally:
            break

    for root, dirs, files in os.walk(TEMPORARY):
        for file in files:
            path = os.path.join(root, file)
            os.remove(path)
