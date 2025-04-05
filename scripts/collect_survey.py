import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import argparse
import pandas as pd
import plotly.express as px
import re

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SELECT_ONE = ["Generation","Denomination","Tech Statement","Tech impact on Church","Tech impact on me"]
SELECT_ALL = ["Church Involvement","Church Engagement","Daily Tech","Devices","When Digital Bibles","Why Digital Bibles","Bible Software","Web Bibles","Mobile Apps","Prayer Apps","Note Apps","Memory Apps"]
SHORT_ANS = ["timestamp","Other Denomination","Other Mobile Apps","Other Prayer Apps","Other Note Apps","Other Memory Apps","Other Tools","Impact"]

def process_data(values):
  """Take the 2d array of data from cells in the google sheet and transform
  it into a pandas dataframe"""
  # Convert the data to a Pandas DataFrame
  columns = ["timestamp","Generation","Denomination","Other Denomination","Church Involvement","Church Engagement","Daily Tech","Tech Statement","Tech impact on Church","Tech impact on me","Devices","When Digital Bibles","Why Digital Bibles","Bible Software","Web Bibles","Mobile Apps","Other Mobile Apps","Prayer Apps","Other Prayer Apps","Note Apps","Other Note Apps","Memory Apps","Other Memory Apps","Other Tools","Impact"]
  df = pd.DataFrame(values[1:], columns=columns)

  # Print the DataFrame
  print("LOADED DATA")
  print(df)
  return df

def bar_graph_generator(df, col, title):
  print(f"GENERATING GRAPH: {title}")
  df_col = df[col].str.get_dummies(sep=', ') # google forms appends multiple checkbox answers with a , and a space
  response_counts = df_col.sum().reset_index()
  response_counts.columns = ['Answer', 'Count']
  response_counts['Answer'] = response_counts['Answer'].astype(str).apply(lambda x: re.sub(r"\(.*?\)", "", x))
  fig = px.bar(response_counts, x='Answer', y='Count',
            text='Count', title=title,
            labels={'Answer': 'Response', 'Count': 'Number of Selections'},
            hover_name='Answer')

  fig.update_traces(textposition='outside')  # Puts count labels above bars
  fig.update_layout(yaxis_title="Count", xaxis_title="Survey Response")  # Optional dark theme

  os.makedirs("./source/_static", exist_ok=True)
  filename= col.replace(' ','_') + '.html'
  fig.write_html(f"./source/_static/{filename}")

def pie_chart_generator(df, col, title):
  print(f"GENERATING GRAPH: {title}")
  # Count each category
  value_counts = df[col].value_counts().reset_index()
  value_counts.columns = ['Answer', 'count']

  # Compute percentage
  value_counts['percent'] = 100 * value_counts['count'] / value_counts['count'].sum()

  # Create pie chart with extra hover info
  fig = px.pie(
      value_counts,
      names='Answer',
      values='count',
      title=title,
      hover_data={'count': True, 'percent': ':.2f'}
  )

  os.makedirs("./source/_static", exist_ok=True)
  filename= col.replace(' ','_') + '.html'
  fig.write_html(f"./source/_static/{filename}")

def main():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  # The ID and range of a sample spreadsheet.
  parser = argparse.ArgumentParser(description="Process some integers.")
  parser.add_argument("--SPREADSHEET_ID", type=str, help="spreadsheet id (get from sheet URL)")
  args = parser.parse_args()
  SAMPLE_SPREADSHEET_ID = args.SPREADSHEET_ID
  SAMPLE_RANGE_NAME = "Responses!A:Y" # grab the entire sheet
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )

    values = result.get("values", [])

    if not values:
      print("No data found.")
      return

    df = process_data(values)

    for col in SELECT_ALL:
      bar_graph_generator(df, col, col)

    for col in SELECT_ONE:
      pie_chart_generator(df, col, col)

  except HttpError as err:
    print(err)

if __name__ == "__main__":
  main()