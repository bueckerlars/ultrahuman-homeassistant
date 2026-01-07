import requests

def main():
    url = "https://partner.ultrahuman.com/api/v1/partner/daily_metrics"
    headers = {
        "Authorization": "eyJhbGciOiJIUzI1NiJ9.eyJzZWNyZXQiOiJmODQyNzVjMGM4NmM1MGQ3ZGRiNiIsInNjb3BlcyI6WyJyaW5nIl0sIm5hbWUiOiJIb21lYXNzaXN0YW50IiwiZXhwIjoxNzk5MzUxMTk2fQ.l-6ZPo5cBgrPiq2FBMZD32KFeBEyfE5pco6PvRd9E5w"
    }

    # Example with date parameter
    params = {
        "date": "2026-01-01"
    }
    response = requests.get(url, params=params, headers=headers)
    print(response.text)

    # Example with epoch parameters
    params = {
        "start_epoch": "1799264396",
        "end_epoch": "1799350796"
    }
    response = requests.get(url, params=params, headers=headers)
    
    print(response.text)


if __name__ == "__main__":
    main()
