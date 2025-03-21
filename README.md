# Zoning Transportation Research Project 
### Author: Rhea Goswami (rkg62) - Junior at Cornell University
### Mentor: Hins Hu
### Advisor: Professor Samitha Samaranayake 

## How to use this repository? 
### Clone the repository 
Clone the repository in your local as it has all the files you need for running shareability.py. 
### Activate Virtual Environment and Install proper requirements 
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

Pretty much, if you hit the play button on the top right of your VSCode, you can run the shareability.py python file. For the default command in the main(), you should see the following print in your console after running for about 5.5 minutes. 
- list of cliques 
- Total Cliques: 115
- Cliques of Size 3: 3
- Cliques of Size 4: 0