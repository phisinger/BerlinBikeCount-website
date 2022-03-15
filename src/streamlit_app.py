import streamlit as st
import os
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(layout='wide',
                   page_title="Cyclists Forecast Berlin",
                   initial_sidebar_state="expanded")

st.image("data/github_image/bike_wide.jpg", use_column_width=True)

st.title("Cyclists Forecast Berlin")
st.markdown("This website presents the forecasted number of cyclists at different locations in Berlin, Germany.  \n \
    On the left, you can select the select counting station and a Date for that you want to predict the number of cyclists.\
    Down, you see different information for this station: The predicted number of cyclists for this date, and some metrics to compare this number.  \n \
    You find the whole code project containing data cleaning, data exploration and forecasting on my [GitHub repo](https://github.com/phisinger/BerlinBikeCount).  \n \
    Disclaimer: Please note that this forecast is based on data from 2012 to 2020, so the years 2021 until 2024 are forecasted.")

# Read in locations
location_data = pd.read_csv("data/prepared-data/location_data.csv")
location_dict = location_data.loc[:, ].to_dict('list')
station_dict = {}
for i in range(len(location_dict['Zaehlstelle'])):
    station_dict.update(
        {location_dict["Beschreibung - Fahrtrichtung"][i]: location_dict['Zaehlstelle'][i]})

# selecting station and prediction date
selected_station = st.sidebar.selectbox(
    "Select your counting station", station_dict.keys())

min_date = datetime.strptime("2021-01-01", '%Y-%m-%d')
max_date = datetime.strptime("2024-08-17", '%Y-%m-%d')

selected_date = st.sidebar.date_input(
    "Select the prediction date", min_value=min_date, max_value=max_date)

# Output

# make two columns
col1, col2 = st.columns(2)

predicted_data = pd.read_csv(filepath_or_buffer="data/predicted-data/" +
                             station_dict[selected_station] + "_predicted_data.csv", parse_dates=["ds"])

col1.markdown("#### Predicted Values")
# yhat for this day
yhat_text = "Forecasted Sum of cyclists on " + selected_date.strftime(
    "%Y-%m-%d") + ": **"
col1.markdown(yhat_text + str(round(predicted_data.loc[predicted_data['ds'].apply(
    lambda x: x.date()) == selected_date, "yhat"].item())) + "**")

# yhat for this week (avg)
week_dataframe = predicted_data.loc[predicted_data['ds'].apply(
    lambda x: x.isocalendar()[:2]) == selected_date.isocalendar()[:2], ["ds", "yhat"]]

week_text = "Average sum of cyclists for the **week** from " + week_dataframe.iloc[0]["ds"].strftime(
    "%Y-%m-%d") + " to " + week_dataframe.iloc[6]["ds"].strftime(
    "%Y-%m-%d") + ": **"
col1.markdown(week_text + str(round(week_dataframe["yhat"].mean())) + "**")

# yhat for this month (avg)
month_dataframe = predicted_data.loc[predicted_data['ds'].apply(
    lambda x: x.timetuple()[:2]) == selected_date.timetuple()[:2], ["ds", "yhat"]]

month_text = "Average sum of cyclists for the **month** from " + month_dataframe.iloc[0]["ds"].strftime(
    "%Y-%m-%d") + " to " + month_dataframe.iloc[-1]["ds"].strftime(
    "%Y-%m-%d") + ": **"
col1.markdown(month_text + str(round(month_dataframe["yhat"].mean())) + "**")

# yhat for this year (avg)
year_dataframe = predicted_data.loc[predicted_data['ds'].apply(
    lambda x: x.year) == selected_date.year, ["ds", "yhat", "yhat_lower", "yhat_upper"]]

year_text = "Average sum of cyclists for the **year** from " + year_dataframe.iloc[0]["ds"].strftime(
    "%Y-%m-%d") + " to " + year_dataframe.iloc[-1]["ds"].strftime(
    "%Y-%m-%d") + ": **"
col1.markdown(year_text + str(round(year_dataframe["yhat"].mean())) + "**")

# map
map_data = (location_data.loc[location_data["Beschreibung - Fahrtrichtung"] == selected_station, [
    "Breitengrad", "Laengengrad"]]).rename(columns={"Breitengrad": "lat", "Laengengrad": "lon"})

col2.markdown("#### Counting station location")
col2.map(data=map_data)

# graph of data throughout the year


def make_yearplot(year_dataframe, selected_date, month_dataframe):
    # create figure
    fig = go.Figure()

    # add yearly graphs
    fig.add_trace(go.Scatter(x=year_dataframe["ds"],
                             y=year_dataframe["yhat_lower"].rolling(
                                 window=7, min_periods=1).mean(),
                             line=dict(color='royalblue',
                                       width=2, dash='dash'),
                             name="Lower predicted sum of cyclists per day (trend)"))
    fig.add_trace(go.Scatter(x=year_dataframe["ds"],
                             y=year_dataframe["yhat_upper"].rolling(
                                 window=7, min_periods=1).mean(),
                             line=dict(color='royalblue',
                                       width=2, dash='dash'),
                             name="Upper predicted sum of cyclists per day (trend)"))
    fig.add_trace(go.Scatter(x=year_dataframe["ds"],
                             y=year_dataframe["yhat"].rolling(
                                 window=7, min_periods=1).mean(),
                             line=dict(color='#ff7f0e', width=2),
                             name="Predicted sum of cyclists per day (trend)"))

    # add month data
    fig.add_trace(go.Scatter(x=month_dataframe["ds"],
                             y=month_dataframe["yhat"],
                             line=dict(color='#00e6ac', width=2),
                             name="Predicted sum of cyclists per day"))

    # add data of selected date
    fig.add_trace(go.Scatter(x=[selected_date],
                             y=month_dataframe.loc[month_dataframe["ds"].apply(
                                 lambda x: x.date()) == selected_date, "yhat"],
                             marker=dict(color="red", size=10),
                             mode="markers",
                             name="Predicted sum of cyclists on selected date"))

    fig.update_layout(title="Cyclists per day throughout the year at selected station",
                      title_font_size=28,
                      xaxis_title="Date",
                      # , legend=dict(y=0, x=0.25),
                      yaxis_title="Sum of cyclists per day",
                      height=600
                      )

    return fig


st.plotly_chart(make_yearplot(year_dataframe, selected_date,
                              month_dataframe), use_container_width=True)
