from bs4 import BeautifulSoup
import urllib.request

def site_irtsu(url):
    response = urllib.request.urlopen(url)
    return response.read()


def pars_irtsu(html):
    soup = BeautifulSoup(html, "lxml")
    head = soup.find_all('p')
    head1 = soup.find_all('font')
    message1 = ['<b>', head[2].text.strip(), ' ', head1[25].text.strip(), '</b>']

    table = soup.find_all('table')

    row = table[1].find_all('tr')
    time = row[1].find_all('td')
    num_less = row[0].find_all('td')
    for i in range(2, 8):
        day = row[i].find_all('td')
        message1.append('\n')
        message1.append('\n')
        message1.append(day[0].text.strip())
        message1.append('\n')
        for j in range(1, 8):
            if day[j].text.strip() == '':
                j += 1
            else:
                message1.append('\n')
                message1.append(num_less[j].text.strip())
                message1.append(' пара ')
                message1.append('\n')
                message1.append('Время: ')
                message1.append(time[j].text.strip())
                message1.append('\n')
                message1.append(day[j].text.strip())
                message1.append('\n')

    message2 = ['\n\n<b>', head[68].text.strip(), ' ', head1[84].text.strip(), '</b>']

    table = soup.find_all('table')

    row = table[2].find_all('tr')
    time = row[1].find_all('td')
    num_less = row[0].find_all('td')
    for i in range(2, 8):
        day = row[i].find_all('td')
        message2.append('\n')
        message2.append('\n')
        message2.append(day[0].text.strip())
        message2.append('\n')
        for j in range(1, 8):
            if day[j].text.strip() == '':
                j += 1
            else:
                message2.append('\n')
                message2.append(num_less[j].text.strip())
                message2.append(' пара ')
                message2.append('\n')
                message2.append('Время: ')
                message2.append(time[j].text.strip())
                message2.append('\n')
                message2.append(day[j].text.strip())
                message2.append('\n')

    sum_mess = message1 + message2
    message_str = ''
    for el in sum_mess:
        message_str += el
    return message_str

