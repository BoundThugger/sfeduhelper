import datetime
import requests
from bs4 import BeautifulSoup

def site_iuas(url):
    response = urllib.request.urlopen(url)
    return response.read()


def iuas_two_tables(html, m, n, p, q):
    soup = BeautifulSoup(html, "lxml")
    head = soup.find_all('p')
    head1 = soup.find_all('font')
    table = soup.find_all('table')

    message1 = ['<b>', head[0].text.strip(), ' ', head1[m].text.strip(), '</b>']
    row = table[n].find_all('tr')
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

    message2 = ['\n\n<b>', head[0].text.strip(), ' ', head1[p].text.strip(), '</b>']
    row = table[q].find_all('tr')
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


def pars_iuas(html):
    temp_now = datetime.datetime.now()
    now = temp_now.date()
    soup = BeautifulSoup(html, "lxml")
    head = soup.find_all('p')
    head1 = soup.find_all('font')
    table = soup.find_all('table')

    if (now > datetime.date(2023, 5, 7)) & (now < datetime.date(2023, 5, 15)):
        return iuas_two_tables(html, 1, 0, 60, 1)

    if (now > datetime.date(2023, 5, 14)) & (now < datetime.date(2023, 5, 22)):
        return iuas_two_tables(html, 60, 1, 119, 2)

    if (now > datetime.date(2023, 5, 21)) & (now < datetime.date(2023, 5, 29)):
        return iuas_two_tables(html, 119, 2, 178, 3)

    if (now > datetime.date(2023, 5, 28)) & (now < datetime.date(2023, 6, 5)):
        return iuas_two_tables(html, 178, 3, 237, 4)

    if (now > datetime.date(2023, 6, 4)) & (now < datetime.date(2023, 6, 12)):
        return iuas_two_tables(html, 237, 4, 296, 5)

    if (now > datetime.date(2023, 6, 11)) & (now < datetime.date(2023, 6, 19)):
        return iuas_two_tables(html, 296, 5, 355, 6)

    if (now > datetime.date(2023, 6, 18)) & (now < datetime.date(2023, 6, 26)):
        return iuas_two_tables(html, 355, 6, 414, 7)

    if (now > datetime.date(2023, 6, 25)) & (now < datetime.date(2023, 7, 3)):
        return iuas_two_tables(html, 414, 7, 473, 8)

    if (now > datetime.date(2023, 7, 2)) & (now < datetime.date(2023, 7, 10)):
        return iuas_two_tables(html, 473, 8, 532, 9)

    if (now > datetime.date(2023, 7, 9)) & (now < datetime.date(2023, 7, 17)):
        message1 = ['<b>', head[0].text.strip(), ' ', head1[532].text.strip(), '</b>']
        row = table[9].find_all('tr')
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

        message_str = ''
        for el in message1:
            message_str += el
        return message_str
