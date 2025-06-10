import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

SETTING = "percentage"

if SETTING == "percentage":
    # Data from the table
    data_baseline_percentage = {
        "max diameter": [1.5, 2, 2.5, 3],
        50: [2.95, 4.25, 6.66, 4.62],
        100: [2.87, 4.09, 5.30, 7.38],
        150: [3.28, 4.94, 6.67, 7.41],
        200: [3.60, 4.37, 6.20, 8.09]
    }

    data_our_percentage = {
        "max diameter": [1.5, 2, 2.5, 3],
        50: [3.47, 5.58, 7.54, 9.15],
        100: [3.31, 6.77, 7.21, 12.41],
        150: [3.57, 5.31, 7.07, 8.59],
        200: [4.10, 5.41, 7.83, 10.24]
    }

    # Convert data to a DataFrame
    df = pd.DataFrame(data_our_percentage)
    df.set_index("max diameter", inplace=True)

    # Transpose the DataFrame to switch axes
    # df = df.T
    vmax_value = 12.5  # Adjust this value based on your comparison needs

    # Create the heatmap
    plt.figure(figsize=(7, 7))
    heatmap = sns.heatmap(
        df,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        cbar_kws={'label': 'Ratio of demand served to total demand'},
        xticklabels=df.columns,
        yticklabels=df.index,
        vmax=vmax_value,
        annot_kws={"size": 16}  # Set annotation font size
    )

    # Customize the color bar label font size
    cbar = heatmap.collections[0].colorbar
    cbar.ax.tick_params(labelsize=16)  # Set tick font size
    cbar.set_label("Ratio of demand served to total demand", fontsize=16)  # Set label font size


    # Add labels and title
    # plt.title("Heatmap of Percentage of Demand Served")
    plt.ylabel("max diameter", fontsize=16)
    plt.xlabel("# of nodes", fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    # Save the plot as an image file
    plt.tight_layout()
    plt.savefig("heatmap_percentage_our.png", dpi=600)

# elif SETTING == "absolute":
#     # Data from the table
#     data_baseline = {
#         "max diameter": [1.5, 2, 2.5, 3],
#         50: [37, 53, 83, 57],
#         100: [144, 205, 265, 369],
#         150: [376, 565, 763, 848],
#         200: [732, 888, 1261, 1643]
#     }

#     data_our = {
#         "max diameter": [1.5, 2, 2.5, 3],
#         50: [43, 69, 93, 113],
#         100: [165, 339, 360, 621],
#         150: [409, 607, 809, 982],
#         200: [834, 1099, 1592, 2080]
#     }


#     # Convert data to a DataFrame
#     df = pd.DataFrame(data_baseline)
#     df.set_index("max diameter", inplace=True)

#     # Transpose the DataFrame to switch axes
#     # df = df.T
#     vmax_value = 2081  # Adjust this value based on your comparison needs

#     # Create the heatmap
#     plt.figure(figsize=(6, 8))
#     sns.heatmap(df, annot=True, fmt=".0f", cmap="YlGnBu", cbar_kws={'label': 'Total Demand Served'},
#                 xticklabels=df.columns, yticklabels=df.index, vmax=vmax_value)

#     # Add labels and title
#     # plt.title("Heatmap of Percentage of Demand Served")
#     plt.ylabel("max diameter", fontsize=14)
#     plt.xlabel("# of nodes", fontsize=14)

#     # Save the plot as an image file
#     plt.tight_layout()
#     plt.savefig("heatmap_baseline.png", dpi=600)
    