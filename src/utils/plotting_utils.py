import matplotlib.pyplot as plt
import numpy as np
from typing import List
import os

from src.config import logger

def plot_fitness_boxplot(fitness_history: List[List[float]], output_path: str = None, query_name: str = ""):
    """
    Plot a boxplot showing fitness spread over generations.
    
    Args:
        fitness_history: List of fitness values for each generation
        output_path: Directory to save the plot (optional)
        query_name: Name of the query for the plot title
    """
    if not fitness_history:
        logger.warning("No fitness history available for plotting")
        return
    
    # Filter out generations with no valid fitness values
    valid_generations = []
    generation_labels = []
    
    for gen_idx, gen_fitness in enumerate(fitness_history):
        if gen_fitness:  # Only include generations with valid fitness values
            valid_generations.append(gen_fitness)
            generation_labels.append(f"Gen {gen_idx}")
    
    if not valid_generations:
        logger.warning("No valid fitness values found for plotting")
        return
    
    # Create the boxplot
    plt.figure(figsize=(12, 6))
    box_plot = plt.boxplot(valid_generations, labels=generation_labels, patch_artist=True)
    
    # Customize the plot
    plt.xlabel('Generation')
    plt.ylabel('Fitness (Cost)')
    title = f'Fitness Distribution Across Generations'
    if query_name:
        title += f' - {query_name}'
    plt.title(title)
    plt.grid(True, alpha=0.3)
    
    # Color the boxes with a gradient
    colors = plt.cm.viridis(np.linspace(0, 1, len(valid_generations)))
    for patch, color in zip(box_plot['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Rotate x-axis labels if there are many generations
    if len(generation_labels) > 10:
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Save the plot if output path is provided
    if output_path:
        os.makedirs(output_path, exist_ok=True)
        filename = f"fitness_boxplot_{query_name}.png" if query_name else "fitness_boxplot.png"
        filepath = os.path.join(output_path, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        logger.info(f"Fitness boxplot saved to: {filepath}")
    
    plt.show()


def plot_fitness_summary_stats(fitness_history: List[List[float]], output_path: str = None, query_name: str = ""):
    """
    Plot summary statistics (min, median, max) of fitness over generations.
    
    Args:
        fitness_history: List of fitness values for each generation
        output_path: Directory to save the plot (optional)
        query_name: Name of the query for the plot title
    """
    if not fitness_history:
        logger.warning("No fitness history available for plotting")
        return
    
    generations = []
    min_fitness = []
    median_fitness = []
    max_fitness = []
    
    for gen_idx, gen_fitness in enumerate(fitness_history):
        if gen_fitness:  # Only include generations with valid fitness values
            generations.append(gen_idx)
            min_fitness.append(min(gen_fitness))
            median_fitness.append(np.median(gen_fitness))
            max_fitness.append(max(gen_fitness))
    
    if not generations:
        logger.warning("No valid fitness values found for plotting")
        return
    
    # Create the line plot
    plt.figure(figsize=(10, 6))
    plt.plot(generations, min_fitness, 'g-', label='Best (Min)', marker='o')
    plt.plot(generations, median_fitness, 'b-', label='Median', marker='s')
    plt.plot(generations, max_fitness, 'r-', label='Worst (Max)', marker='^')
    
    # Fill between min and max for visual effect
    plt.fill_between(generations, min_fitness, max_fitness, alpha=0.2, color='gray')
    
    plt.xlabel('Generation')
    plt.ylabel('Fitness (Cost)')
    title = f'Fitness Statistics Over Generations'
    if query_name:
        title += f' - {query_name}'
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the plot if output path is provided
    if output_path:
        os.makedirs(output_path, exist_ok=True)
        filename = f"fitness_stats_{query_name}.png" if query_name else "fitness_stats.png"
        filepath = os.path.join(output_path, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        logger.info(f"Fitness statistics plot saved to: {filepath}")

    plt.show()
