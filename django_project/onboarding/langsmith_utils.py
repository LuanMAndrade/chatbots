# django_project/onboarding/langsmith_utils.py

import os
from datetime import datetime, timedelta
from langsmith import Client
import logging
import calendar

logger = logging.getLogger(__name__)

dolar = 6

def get_langsmith_client():
    """Initializes the LangSmith client."""
    try:
        client = Client(
            api_key=os.getenv('LANGSMITH_API_KEY'),
            api_url=os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')
        )
        return client
    except Exception as e:
        logger.error(f"Error connecting to LangSmith: {e}")
        return None

def get_month_period(year, month, billing_day=5):
    """Calculates the month's period based on the billing day."""
    current_date = datetime.now()
    current_day = current_date.day

    if current_day >= billing_day:
        month += 1

    
    if month == 1:
        start_year = year - 1
        start_month = 12
    else:
        start_year = year
        start_month = month - 1
    
    start_time = datetime(start_year, start_month, billing_day, 0, 0, 0)
    
    # Data de fim: dia anterior ao dia de cobrança do mês atual
    end_day = billing_day - 1
    if end_day == 0:
        if month == 12:
            end_year = year + 1
            end_month = 1
        else:
            end_year = year
            end_month = month + 1
        end_day = calendar.monthrange(end_year, end_month)[1]  # Último dia do mês
    else:
        end_year = year
        end_month = month
    
    end_time = datetime(end_year, end_month, end_day, 23, 59, 59)
    
    return start_time, end_time


def get_available_months(billing_day=5):
    """
    Retorna os meses disponíveis baseado no dia de cobrança
    """
    current_date = datetime.now()
    current_day = current_date.day
    
    # Se ainda não passou do dia de cobrança, o mês atual ainda não começou
    if current_day < billing_day:
        # Estamos no período do mês anterior
        if current_date.month == 1:
            current_year = current_date.year - 1
            current_month = 12
        else:
            current_year = current_date.year
            current_month = current_date.month - 1
    else:
        # Estamos no período do mês atual
        current_year = current_date.year
        current_month = current_date.month

    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    months = []
    
    # Adiciona os últimos 12 meses
    for i in range(12):
        month = current_month - i
        year = current_year
        
        while month <= 0:
            month += 12
            year -= 1
        
        month_name = meses_pt.get(month)
        months.append({
            'value': f"{year}-{month:02d}",
            'label': f"{month_name} {year}",
            'year': year,
            'month': month
        })
    
    return months


def get_token_usage_for_period(project_name, start_time, end_time):
    """Extracts token usage metrics from LangSmith for a given period."""
    client = get_langsmith_client()
    if not client:
        raise Exception("Could not connect to LangSmith.")

    runs = list(client.list_runs(
        project_name=project_name,
        start_time=start_time,
        end_time=end_time,
        run_type="chain" # Only fetch parent runs to count executions
    ))

    # CORRECTED CODE
    total_stats = client.get_run_stats(
    project_names=[project_name], # <-- LIKE THIS
    start_time=start_time,
    end_time=end_time
    )

    # Safely access total_tokens, providing a default of 0 if not found
    total_tokens = total_stats.get('total_tokens', 0)
    prompt_tokens = total_stats.get('prompt_tokens', 0)
    completion_tokens = total_stats.get('completion_tokens', 0)
    total_cost = total_stats.get('total_cost', 0)

    return {
        'input_tokens': prompt_tokens,
        'output_tokens': completion_tokens,
        'total_tokens': total_tokens,
        'total_cost': total_cost * dolar,
        'run_count': len(runs),
        'period_start': start_time.isoformat(),
        'period_end': end_time.isoformat(),
    }

def get_daily_usage_breakdown(project_name, start_time, end_time):
    """Returns a daily breakdown of token usage for a specific period."""
    client = get_langsmith_client()
    if not client:
        raise Exception("Could not connect to LangSmith.")

    daily_data = {}
    current_day = start_time
    while current_day <= end_time:
        day_str = current_day.strftime('%Y-%m-%d')
        daily_data[day_str] = {
            'date': day_str,
            'total_tokens': 0, 'input_tokens': 0, 'output_tokens': 0,
            'cost': 0, 'run_count': 0
        }
        current_day += timedelta(days=1)

    runs = list(client.list_runs(
        project_name=project_name,
        start_time=start_time,
        end_time=end_time,
        run_type="chain"
    ))

    for run in runs:
        if run.start_time:
            day_str = run.start_time.strftime('%Y-%m-%d')
            if day_str in daily_data:
                daily_data[day_str]['run_count'] +=1
                if run.total_tokens:
                    daily_data[day_str]['total_tokens'] += run.total_tokens
                if run.prompt_tokens:
                    daily_data[day_str]['input_tokens'] += run.prompt_tokens
                if run.completion_tokens:
                    daily_data[day_str]['output_tokens'] += run.completion_tokens
                if run.total_cost:
                    daily_data[day_str]['cost'] += run.total_cost

    daily_data[day_str]['cost'] *= dolar
    return sorted(daily_data.values(), key=lambda x: x['date'])
    