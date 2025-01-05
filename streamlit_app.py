###################################
# check flight number
###################################
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import streamlit as st

# URL of the arrivals/departures page (you need to check the actual page URL)
ref = "TU723"
task_date = "2025-01-05"
url = f"https://www.aeroport-de-tunis-carthage.com/tunisie-aeroport-de-tunis-carthage-vol-arrivee-numero-{ref}-date-{task_date}"

# Send request to the website
response = requests.get(url)
print("------------------------------")
print("------------------------------")
print(response.content)
print("------------------------------")
print("------------------------------")


# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")
    #soup = BeautifulSoup(html_content, 'html.parser')

    # Find the table containing the flight data
    table = soup.find('table', width="100%")
    print("######## table: ")
    print(table)
    print("=======================================================")
    # Extract the rows of the table (excluding the header row)
    rows = table.find_all('tr')[1:]
    print("######## rows: ")
    print(rows)
    print("=======================================================")

    # Prepare a list to store the data
    flight_data = []

    # Loop through each row and extract the relevant columns
    row = rows[0]
    cells = row.find_all('td')
    print(f"###### cells with len = {len(cells)} ")
    print(cells)
    print(type(cells))
    print("=======================================================")

#Date	Heure Locale	Origine	Compagnie	N° de Vol	Statut	Ponctualité
    for i in range(len(cells)//7):
        flight_date = cells[i+6*i].get_text(strip=True)
        local_time = cells[i+1+6*i].get_text(strip=True)
        origin = cells[i+2+6*i].get_text(strip=True)
        company = cells[i+3+6*i].get_text(strip=True)
        flight_number = cells[i+4+6*i].get_text(strip=True)
        status = cells[i+5+6*i].get_text(strip=True)
        Ponctuality = cells[i+6+6*i].get_text(strip=True)

        # Store the extracted data in the list
        flight_data.append({
            'Date': flight_date,
            'Heure Locale': local_time,
            'Origine': origin,
            'Compagnie': company,
            'N° de Vol': flight_number,
            'Statut': status,
            'Ponctualité': Ponctuality
        })

    # Output the extracted flight data
    for flight in flight_data:
        print(flight)
#{'Date': '2024-12-15', 'Heure Locale': '19:55:00', 'Origine': 'PARIS ORLY', 'Compagnie': 'TUNISAIR', 'N° de Vol': 'TU723', 'Statut': 'ATTERRI 21:33', 'Ponctualité': 'Retard de 1 heure et 38 minutes'}
#{'Date': '2024-12-14', 'Heure Locale': '19:25:00', 'Origine': 'PARIS ORLY', 'Compagnie': 'TUNISAIR', 'N° de Vol': 'TU723', 'Statut': 'ATTERRI 20:20', 'Ponctualité': 'Retard de 55 minutes'}
#{'Date': '2024-12-13', 'Heure Locale': '20:35:00', 'Origine': 'PARIS ORLY', 'Compagnie': 'TUNISAIR', 'N° de Vol': 'TU723', 'Statut': 'ANNULE', 'Ponctualité': 'ANNULE'}




# Sample data with special cases


    # Convert JSON to DataFrame
    df = pd.DataFrame(flight_data)

    # Function to convert delay string to minutes
    def parse_delay(delay_str):
        if delay_str == 'ANNULE':
            return None  # Use None for canceled flights
        if delay_str == 'Aucun retard':
            return 0  # No delay
        match = re.match(r"Retard de (\d+) heure(?:s)? et (\d+) minute(?:s)?", delay_str)
        if match:
            hours, minutes = map(int, match.groups())
            return hours * 60 + minutes
        match = re.match(r"Retard de (\d+) minute(?:s)?", delay_str)
        if match:
            return int(match.group(1))
        return 0  # Default to no delay

    # Add a new column for delay in minutes
    df['Delay (minutes)'] = df['Ponctualité'].apply(parse_delay)

    # Handle canceled flights for metrics
    df['Is Canceled'] = df['Ponctualité'] == 'ANNULE'
    df['Is On Time'] = df['Delay (minutes)'] == 0
    # Categorize delays
    def classify_delay(delay):
        if delay == 0:
            return 'No Delay'
        elif delay < 60:
            return 'Delay < 1 hour'
        elif 60 <= delay <= 180:
            return 'Delay 1-3 hours'
        elif delay > 180:
            return 'Delay > 3 hours'
        else:
            return 'Canceled'
        

    df['Delay Category'] = df['Delay (minutes)'].apply(classify_delay)

    # Calculate percentages for the categories
    # category_counts = df['Delay Category'].value_counts(normalize=True) * 100 # en pourcentages
    category_counts = df['Delay Category'].value_counts() # simple count

    # Streamlit Dashboard
    st.title(f"_TUNISAIR_ dashboard for flight :blue[{ref}] over the last 30 days")

    # Metrics
    total_flights = len(df)
    canceled_flights = df['Is Canceled'].sum()
    on_time_flights = df['Is On Time'].sum()
    average_delay = df['Delay (minutes)'].mean(skipna=True)

    st.metric("Total Flights", total_flights)
    st.metric("Canceled Flights", canceled_flights)
    st.metric("On-Time Flights", on_time_flights)
    st.metric("Average Delay (minutes)", round(average_delay, 2))

    # Visualizations
    st.subheader("Delays Over Time (in minutes)")
    st.line_chart(df.set_index('Date')['Delay (minutes)'])

    st.subheader("Flight Status Breakdown")
    status_counts = df['Ponctualité'].value_counts()
    st.bar_chart(status_counts)

    st.subheader("Delay Categories Breakdown")
    st.write("Distribution of delays across different categories")
    st.dataframe(category_counts)
    # Pie Chart for Delay Categories
    st.subheader("Pie Chart Delay Categories (Percentage)")
    st.pyplot(category_counts.plot.pie(
        autopct='%1.1f%%', figsize=(6, 6), title="Delay Categories"
    ).get_figure())


    st.subheader("Detailed Flight Data")
    st.table(df[['Date', 'Heure Locale', 'Origine', 'Compagnie', 'N° de Vol', 'Statut', 'Ponctualité', 'Delay (minutes)', 'Delay Category']])


else:
    print("Failed to retrieve the webpage. Status code:", response.status_code)

