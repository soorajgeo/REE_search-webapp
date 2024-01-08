
# REEsearch_webapp

Web application built with Pywebio to find matching REE minerals from the database of webmineral.com using EPMA data



## Usage and methodology
This application can be used if your EPMA data contains atleast one of the REE bearing elements (La to Lu, Y and Sc) in weight percent oxides. The database for REE bearing minerals were created by webscraping [webmineral.com](https://webmineral.com/) using the [beautiful-soup](https://beautiful-soup-4.readthedocs.io/en/latest/) python library.  
The user can upload a csv file containing the elemental oxide weight percent data (usually EPMA data) in columns and the point analysis as rows. Make sure the total for each point analysis is close to 100%. The application also displays the demo csv format in its first window for reference. 

The application uses simple vector algebra method known as cosine similarity (https://en.wikipedia.org/wiki/Cosine_similarity) to identify the minerals from the database. First it converts the user data into vectors (vectors can be any dimension- this is why you can search for minerals with any number of elements in its composition) and compare against the REE database (REE_data.csv) and displays the result which the user can download as csv. The user can also click any rows of the result window to compare their data with the REE database. See the below gif to see how the application runs.

## Python libraries used

- Scikit-learn for performing pairwise cosine similarity search
- Pywebio for designing the web application
- numpy and pandas for data wrangling


## Demo
[]![REE_web_app](https://github.com/soorajgeo/REE_search-webapp/assets/51475605/01b9e1a7-d235-4db4-aab6-0c6b6ae02896)




    
