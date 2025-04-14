# Zoning Transportation Research Project 
#### Author: Rhea Goswami (rkg62) - Junior at Cornell University
#### Mentor: Hins Hu
#### Advisor: Professor Samitha Samaranayake 

## How to Use this Repository? 
### Clone the Repository 
Clone the repository in your local as it has all the files you need for running shareability.py. 
### Activate Virtual Environment and Install Proper Requirements 
For MacOS/Linux, you can activate the virtual environment by using the source command. 
    source venv/bin/activate

For Windows, you can activate the virtual environment in your command prompt by using
    myvenv\Scripts\activate. 

This virtual environment should come with all the dependencies already downloaded in its lib folder. However, if that doesn't work for you, there is a requirements.txt file, which you can download to your local. 
    pip install -r requirements.txt

### Run the Code
In shareability.py, you will see that there is a main() function. This function is what you will primarily alter to see different results. The current default that actually runs the clique generation is the following command. 
        lst = generate_shared_trips_more(len(data_reduced), 3, 5, data_reduced)
Here, we have a maximum cardinality of 3 for the cliques and the maximum diameter for each clique is 5 km. The other line that you can change in main() is the csv file that is being read. 
    filepath = os.path.join(os.path.dirname(__file__), "new_synthetic_data.csv")
    df = pd.read_csv(filepath)
I provide two synthetic data files in the repository, and it can be changed to see different results. 

Pretty much, if you hit the play button on the top right of your VSCode, you can run the shareability.py python file or you can do it from the terminal by calling "python shareability.py". For the default command in the main(), you should see the following print in your console after running for about 5.5 minutes (as of 3/21). 

##### Expected Output:

    h_geocode     w_geocode  ...                                               line  distance_kilometers
    0    470650112033  470650113214  ...  LINESTRING (-85.05276256397683 35.005649318052...             0.452896
    1    470650114475  470650114451  ...  LINESTRING (-85.11318749999286 35.115935750020...             5.224514
    2    470650114483  470650024003  ...  LINESTRING (-85.15299687905201 35.053180336887...             6.683063
    3    470650110043  470650114451  ...  LINESTRING (-85.37702500746178 35.147019981186...             2.798276
    4    470650101032  470650114462  ...  LINESTRING (-85.05427781321548 35.217505548519...             6.190115
    ..            ...           ...  ...                                                ...                  ...
    295  470650114021  470650031002  ...  LINESTRING (-85.20094440073969 35.082049945027...             4.668057
    296  470650113254  470650123003  ...  LINESTRING (-85.11893771929668 34.988952986502...             3.573838
    297  470650101013  470659802001  ...  LINESTRING (-85.05546642826265 35.181060586951...             0.538910
    298  470650114132  470650124002  ...  LINESTRING (-85.13315440772966 35.115133556635...             6.582079
    299  470650113213  470659801001  ...  LINESTRING (-85.13152811182067 35.026697925918...             0.842991

    [300 rows x 11 columns]
            h_geocode     w_geocode  ...                                               line  distance_kilometers
    0    470650112033  470650113214  ...  LINESTRING (-85.05276256397683 35.005649318052...             0.452896
    1    470650110043  470650114451  ...  LINESTRING (-85.37702500746178 35.147019981186...             2.798276
    2    470650113141  470650112032  ...  LINESTRING (-85.10751257723447 35.041392713374...             0.520741
    3    470650113254  470650104324  ...  LINESTRING (-85.12013218049088 34.990363307393...             3.120379
    4    470650114441  470650114021  ...  LINESTRING (-85.21803465717514 35.055297330593...             1.974639
    ..            ...           ...  ...                                                ...                  ...
    244  470650104326  470659802001  ...  LINESTRING (-85.22969878028485 35.141889167347...             2.514551
    245  470650114021  470650031002  ...  LINESTRING (-85.20094440073969 35.082049945027...             4.668057
    246  470650113254  470650123003  ...  LINESTRING (-85.11893771929668 34.988952986502...             3.573838
    247  470650101013  470659802001  ...  LINESTRING (-85.05546642826265 35.181060586951...             0.538910
    248  470650113213  470659801001  ...  LINESTRING (-85.13152811182067 35.026697925918...             0.842991

    [249 rows x 11 columns]
    [(2, 235), (2, 240), (3, 170), (4, 108), (4, 109), (6, 112), (6, 180), (7, 197), (9, 160), (10, 153), (10, 193), (12, 63), (12, 178), (14, 203), (19, 183), (20, 120), (21, 166), (22, 219), (24, 158), (24, 174), (24, 186), (24, 237), (26, 171), (27, 176), (28, 74), (28, 144), (28, 224), (33, 101), (35, 156), (36, 159), (36, 172), (37, 72), (37, 123), (40, 76), (40, 104), (45, 153), (45, 193), (46, 48), (47, 72), (47, 122), (48, 166), (49, 159), (52, 208), (54, 187), (55, 97), (55, 200), (56, 118), (59, 157), (59, 227), (63, 178), (64, 168), (66, 95), (66, 219), (67, 134), (69, 243), (70, 93), (71, 129), (74, 82), (74, 184), (74, 224), (75, 184), (75, 224), (76, 128), (80, 100), (81, 241), (82, 144), (84, 142), (87, 142), (89, 154), (90, 144), (90, 248), (91, 122), (91, 233), (92, 164), (92, 195), (97, 222), (100, 188), (101, 200), (104, 128), (105, 122), (105, 233), (106, 210), (107, 129), (108, 109), (113, 114), (119, 120), (119, 143), (119, 248), (120, 122), (120, 248), (125, 192), (129, 191), (132, 170), (137, 224), (137, 248), (141, 155), (144, 184), (148, 214), (149, 191), (152, 243), (156, 207), (158, 186), (161, 192), (162, 233), (166, 183), (166, 225), (172, 206), (174, 237), (179, 241), (187, 240), (188, 229), (238, 241), (12, 63, 178), (24, 158, 186), (28, 74, 224)]     
    115
    Counter 3: 3
    Counter 4: 0