import datetime as dt
from django.shortcuts import render

def year(request):
    """
    Добавляет переменную с текущим годом.
    """
    current_year = dt.datetime.today().year
    return {'year': current_year}
