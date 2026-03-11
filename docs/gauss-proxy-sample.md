# Gauss 활용시 프록시 설정 예제

proxies = { ‘http':None, ‘https’:None}

response = requests.get( api_endpoint_url, headers=headers, proxies=proxies, verify=False) 