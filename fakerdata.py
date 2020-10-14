import os
import pathlib
import random
import sys
from datetime import timedelta

import django
from django.apps import apps
from django.utils import timezone

from faker import Faker

# 将项目根目录添加到 Python 的模块搜索路径中，这样在运行脚本时 Python 才能够找到相应的模块并执行
back = os.path.dirname
BASE_DIR = back(back(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append('/home/jeff/.venvs/locallib/lib/python3.8/site-packages')
print(sys.path)

if __name__ == "__main__":
    # 设置 DJANGO_SETTINGS_MODULE 环境变量，这将指定 django 启动时使用的配置文件
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "locallib.settings")
		# 启动 django，到目前为止就是启动 Django 的必要条件
    django.setup()

    from catalog.models import Book, BookInstance, Author, Genre

    print("create genre")
    Genre.objects.create(name="IT")
    Genre.objects.create(name="Politics")
    Genre.objects.create(name="Psychology")

    fake = Faker()

    for _ in range(100):
        first_name=fake.name()
        last_name=fake.name()
        birthday=fake.date_time_between(
            start_date="-100y", end_date="-30y", tzinfo=timezone.get_current_timezone()
        )
        Author.objects.create(first_name=first_name, last_name=last_name, date_of_birth=birthday)


    print("create book")
    for author in Author.objects.all()[:80]:
        books = random.randint(1,10)
        for _ in range(books):
            gen=random.choice(Genre.objects.all())
            lang=random.choice(['en','zh','fr','de','es','ja'])

            cbook = Book.objects.create(title=fake.sentence(), summary=fake.paragraphs(2),isbn=random.randint(200000000,8000000000),
            language=lang, author=author)
            cbook.genre.add(gen)

   
    print("done!")