import json
import urllib.request, urllib.parse


def read_bing_key():
    bing_api_key = None
    try:
        with open('bing.key', 'r') as f:
            bing_api_key = f.readline();
    except:
        raise IOError('bing.key file not found')

    return bing_api_key


def run_query(search_terms):
    bing_api_key = read_bing_key()
    if not bing_api_key:
        raise KeyError("Bing Key Not Found")
    root_url = 'https://api.datamarket.azure.com/Bing/Search/'
    service = 'Web'
    results_per_page = 10
    offset = 0

    query = "'{0}'".format(search_terms)
    query = urllib.parse.quote(query)
    search_url = "{0}{1}?$format=json&$top={2}&$skip={3}&Query={4}".format(
        root_url,
        service,
        results_per_page,
        offset,
        query)

    username = ''
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, search_url, username, bing_api_key)

    results = []

    try:
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(handler)
        urllib.request.install_opener(opener)
        response = urllib.request.urlopen(search_url).read()
        response = response.decode('utf-8')

        json_response = json.loads(response)

        for result in json_response['d']['results']:
            results.append({'title': result['Title'],
                            'link': result['Url'],
                            'summary': result['Description']})
    except:
        print("Error when querying the Bing API")

    return results


def main():
    search_terms = input()
    results = run_query(search_terms)
    print(results)


if __name__ == '__main__':
    main()
