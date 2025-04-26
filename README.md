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
__[Hins] Something below is inconsistent with your code. Make modification.__

In shareability.py, you will see that there is a main() function. This function is what you will primarily alter to see different results. The current default that actually runs the clique generation is the following command. 
        lst = generate_shared_trips_more(len(data_reduced), 4, 5, data_reduced)
Here, we have a maximum cardinality of 4 for the cliques and the maximum diameter for each clique is 5 km. The other line that you can change in main() is the csv file that is being read. 
    filepath = os.path.join(os.path.dirname(__file__), "new_synthetic_data.csv")
    df = pd.read_csv(filepath)
I provide two synthetic data files in the repository, and it can be changed to see different results. 

Pretty much, if you hit the play button on the top right of your VSCode, you can run the shareability.py python file or you can do it from the terminal by calling "python shareability.py". For the default command in the main(), you should see the following print in your console. 

##### Expected Output:
        h_geocode  ...  distance_kilometers
0    470650112033  ...             0.452896
1    470650114475  ...             5.224514
2    470650114483  ...             6.683063
3    470650110043  ...             2.798276
4    470650101032  ...             6.190115
..            ...  ...                  ...
295  470650114021  ...             4.668057
296  470650113254  ...             3.573838
297  470650101013  ...             0.538910
298  470650114132  ...             6.582079
299  470650113213  ...             0.842991

[300 rows x 11 columns]
        h_geocode  ...  distance_kilometers
0    470650112033  ...             0.452896
1    470650110043  ...             2.798276
2    470650113141  ...             0.520741
3    470650113254  ...             3.120379
4    470650114441  ...             1.974639
..            ...  ...                  ...
244  470650104326  ...             2.514551
245  470650114021  ...             4.668057
246  470650113254  ...             3.573838
247  470650101013  ...             0.538910
248  470650113213  ...             0.842991

[249 rows x 11 columns]
[(2, 235), (2, 240), (3, 170), (4, 108), (4, 109), (6, 35), (6, 112), (6, 180), (7, 197), (8, 97), (8, 158), (9, 160), (10, 153), (10, 193), (12, 63), (12, 178), (14, 203), (19, 183), (20, 120), (21, 166), (22, 66), (22, 113), (22, 219), (23, 104), (24, 55), (24, 158), (24, 174), (24, 186), (24, 237), (25, 50), (25, 215), (25, 221), (26, 171), (27, 94), (27, 176), (28, 74), (28, 102), (28, 144), (28, 184), (28, 224), (30, 94), (33, 41), (33, 101), (35, 156), (36, 159), (36, 172), (37, 72), (37, 82), (37, 102), (37, 120), (37, 123), (37, 143), (40, 76), (40, 104), (42, 142), (45, 153), (45, 193), (46, 48), (47, 72), (47, 91), (47, 105), (47, 119), (47, 122), (47, 162), (48, 51), (48, 166), (49, 159), (51, 185), (52, 208), (54, 187), (54, 192), (55, 97), (55, 101), (55, 200), (56, 118), (59, 157), (59, 227), (60, 97), (60, 222), (63, 178), (64, 168), (66, 95), (66, 219), (67, 134), (69, 243), (70, 93), (71, 129), (74, 82), (74, 184), (74, 224), (75, 184), (75, 224), (76, 128), (80, 100), (81, 194), (81, 241), (82, 144), (84, 142), (87, 142), (89, 154), (90, 119), (90, 137), (90, 144), (90, 248), (91, 105), (91, 122), (91, 162), (91, 233), (92, 164), (92,), (119, 143), (119, 248), (120, 122), (120, 248), (125, 192), (127, 220), (129, 191), (132, 170), (136, 223), (137, 224), (137, 248), (139, 151), (141, 155), (144, 184), (148, 214), (149, 191), (152, 243), (156, 207), (158, 186), (161, 192), (162, 233), (166, 183), (166, 225), (172, 206), (174, 237), (179, 238), (179, 241), (187, 240), (188, 229), (189, 242), (194, 236), (194, 241), (202, 204), (235, 240), (238, 241), (2, 235, 240), (4, 108, 109), (12, 63, 178), (22, 113, 219), (24, 237, 186), (24, 237, 158), (24, 186, 158), (27, 94, 176), (28, 224, 74), (28, 224, 144), (28, 74, 144), (36, 159, 172), (37, 72, 143), (37, 72, 123), (40, 76, 104), (47, 105, 122), (47, 105, 91), (47, 122, 91), (48, 51, 166), (55, 200, 97), (60, 97, 222), (66, 95, 219), (75, 184, 224), (90, 137, 248), (91, 105, 122), (91, 105, 233), (91, 122, 233), (92, 164, 195), (105, 122, 233), (119, 120, 248), (119, 137, 248), (119, 248, 143), (120, 122, 248), (28, 224, 74, 144)]
193
Counter 3: 33
Counter 4: 1