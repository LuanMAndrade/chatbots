# django_project/onboarding/langsmith_utils.py

import os
from datetime import datetime, timedelta
from langsmith import Client
import logging
import calendar

logger = logging.getLogger(__name__)

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
    start_date_of_month = datetime(year, month, 1)

    # Determine the start of the period
    if start_date_of_month.month == 1:
        start_time = datetime(start_date_of_month.year - 1, 12, billing_day)
    else:
        start_time = datetime(start_date_of_month.year, start_date_of_month.month - 1, billing_day)

    # Determine the end of the period
    end_time = datetime(year, month, billing_day - 1, 23, 59, 59)

    return start_time, end_time


def get_available_months(billing_day=5):
    """Returns available months based on the billing day."""
    months = []
    # Start from the current month or previous month depending on billing day
    today = datetime.today()
    current_month = today.month
    current_year = today.year

    if today.day < billing_day:
        if current_month == 1:
            current_month = 12
            current_year -= 1
        else:
            current_month -= 1

    for i in range(12):
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1

        month_name = calendar.month_name[month]
        months.append({
            'value': f"{year}-{month:02d}",
            'label': f"{month_name} {year}",
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
        'total_cost': total_cost,
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

    return sorted(daily_data.values(), key=lambda x: x['date'])