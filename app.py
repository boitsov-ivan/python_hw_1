import streamlit as st
import requests
import json
import os
import pandas as pd
import io
import matplotlib.pyplot as plt
import seaborn as sns



from datetime import date, time, datetime
import matplotlib.dates as mdates





def analise_data(city):
    A = df[df['city'] == city]['temperature']
    B = df[df['city'] == city]['temperature'].rolling(window=30).mean()
    Date = df['timestamp'][df['city'] == city]
    #записываем скользящее среднее для города
    df.loc[A.index, 'Скользящее среднее температуры (30 дней)'] = B.copy()
    #запишем среднюю температуру и стандартное отклонение для каждого сезона в городе
    df.loc[A.index, 'Средняя температура по сезону'] = df[df['city']== city].groupby(['season'])['temperature'].transform(lambda x: x.mean())

    df.loc[A.index, 'Cтандартное отклонение температуры по сезону'] = df[df['city']== city].groupby(['season'])['temperature'].transform(lambda x: x.std())

    #выявляем аномалии, где температура выходит за пределы  среднее ± 2σ
    df.loc[A.index, 'Аномалия по сезону'] = df[df['city']== city].groupby(['season'])['temperature'].transform(lambda x: (x > (x.mean() + 2* x.std())) | (x < (x.mean() -2* x.std())))
    


def draw(data):
    start = 0
    stop = 365

    temp = data['temperature'][start:stop]
    dates = data['timestamp'][start:stop]


    temp_abnormal = data['temperature'][start:stop][data['Аномалия по сезону'] == True]
    date_abnormal = data['timestamp'][start:stop][data['Аномалия по сезону'] == True]

    B = temp.rolling(window=30).mean()



    events = []
    abnormal_events = []
    for i in dates:
        date_string = i
        format = '%Y-%m-%d'  # указываем формат строки даты
        d = datetime.strptime(date_string, format)
        dt = datetime(d.year, d.month, d.day)
        events.append(dt)
        if i in date_abnormal.tolist():
            abnormal_events.append(dt)


    months = mdates.MonthLocator()
    days = mdates.DayLocator()
    timeFmt = mdates.DateFormatter('%Y-%m')


    fig, ax = plt.subplots(figsize=(20, 10))
    plt.plot(events, temp)
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(timeFmt)
    ax.xaxis.set_minor_locator(days)



    plt.title(f"Динамика изменения температуры в {city} c указанием сезонных аномалий")

    plt.plot(temp, 'b',  label="Суточная температура")
    plt.plot(temp_abnormal, 'ro',  label="Аномалии")

    plt.plot(B, 'g--',  label="30-дневная скользящая средняя температура")





    for f, b, i in zip(abnormal_events, temp_abnormal.tolist(), date_abnormal):
        if b > 0:
            stroka = i + ' ' + '+' + str(round(b, 2)) + ' ℃'
        else:
            stroka = i + ' ' + str(round(b, 2)) + ' ℃'
        plt.text(f,b,stroka, size = 'x-small', ha = 'center')



    plt.legend() 
    #plt.show()
    return fig


def simple_draw(data):
    
    
    start = 0
    stop = 365

    temp = data['temperature'][start:stop]
    dates = data['timestamp'][start:stop]
    fig, ax = plt.subplots(figsize=(20, 10))


    temp_abnormal = data['temperature'][start:stop][data['Аномалия по сезону'] == True]
    date_abnormal = data['timestamp'][start:stop][data['Аномалия по сезону'] == True]

    B = temp.rolling(window=30).mean()


    plt.title(f"Динамика изменения температуры в {city} c указанием сезонных аномалий за первые 365 дней данных")

    plt.plot(temp, 'b',  label="Суточная температура")
    plt.plot(temp_abnormal, 'ro',  label="Аномалии")

    plt.plot(B, 'g--',  label="30-дневная скользящая средняя температура")
    
    


    plt.legend() 
    #plt.show()
    return fig










st.title("Анализ температурных данных и мониторинг текущей температуры через OpenWeatherMap API")




# Выбор города для анализа
city = st.selectbox("Для какого города выполнить анализ?", ('New York', 'London', 'Paris', 'Tokyo', 'Moscow', 'Sydney', 'Berlin', 'Beijing', 'Rio de Janeiro', 'Dubai', 'Los Angeles', 'Singapore', 'Mumbai', 'Cairo', 'Mexico City'), index=4,)
st.write("Вы выбрали:", city)

# Ввод ключа для API
api_key = st.text_input("Введите API-ключ OpenWeatherMap:", "API-ключ")  


# Вкладка для загрузки данных из файла
st.subheader("Загрузка файла с историческими данными")
uploaded_file = st.file_uploader("Загрузите CSV файл", type="csv")


if st.button(f"Выполнить анализ исторических данных, вывести текущую температура для {city } через API и определить, нормальна ли она для сезона"):
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
            if df.empty:
                st.error("DataFrame пустой. Проверьте содержимое CSV файла.")
            else:
                #st.write(df.head())
                cities = df['city'].unique().tolist()
                for c in cities:
                    analise_data(c)
                #st.write(df.head())
                data = df[df['city'] == city]
                if city == 'Moscow':
                    st.pyplot(draw(data))
                else:
                    st.pyplot(simple_draw(data))
                for i in data['season'].unique().tolist():
                    st.write(f"Профиль {i} с указанием среднего и стандартного отклонения для города {city}:")
                    st.write( data[data['season'] == i][['temperature', 'Скользящее среднее температуры (30 дней)']].describe())
                
                st.write(f"Описательные статистики по всем историческим данным для города {city}:")
                st.write( data[['temperature', 'Скользящее среднее температуры (30 дней)']].describe())
                
                
                
               
                url = "http://api.openweathermap.org/data/2.5/weather?"+ "appid=" + api_key + "&q=" + city
                    

                # Получаем текущую дату и время
                now = datetime.now()

                # Определяем сезон на основе текущего месяца
                if now.month in (1, 2, 12):
                    current_season = 'winter'
                elif now.month in (3, 4, 5):
                    current_season = 'spring'
                elif now.month in (6, 7, 8):
                    current_season = 'summer'
                else:
                    current_season = 'autumn'
                    
                # Выводим на экран текущее время года
                st.write(f'Текущее вреся года: {current_season}')
                response = requests.get(url)
                x = response.json()
                if x["cod"] == 200:
                    st.write(f"Получены данные с {url}. Код ответа сервера: {x["cod"]}")
                    y = x["main"]
                    st.write(f"Температура в {x["name"]} в кельвинах: {y["temp"]}")
                    temp = y["temp"] - 273.15
                    st.write(f"Температура в {x["name"]} в градусах Цельсия: {temp}")
                    
                    m = df[ (df['city']== x["name"]) & (df['season'] == current_season)]['temperature'].mean()
                    stdd = df[ (df['city']== x["name"]) & (df['season'] == current_season)]['temperature'].std()
        
                    if (temp > (m +  2* stdd) ) | (temp < (m -2* stdd) ):
                        st.write("!!! Текущая температура в городе является аномальной !!!")
                    else:
                        st.write("Текущая температура в городе не является аномальной.")
                else:
                    st.write(f"Ошибка запроса: {x["cod"]}")
                    st.write(f"{x["message"]}")
        except:
            st.error("Файл не удалось прочесть.")
            
    else:
        st.warning("Пожалуйста, загрузите CSV файл.")

            
                
    


    
    
    


