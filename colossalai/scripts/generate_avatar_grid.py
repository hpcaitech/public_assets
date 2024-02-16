import argparse
import json
import math
import requests
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw
import random


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    return parser.parse_args()

def get_contributor_avatars(repo):
    github_api = f"https://api.github.com/repos/{repo}/stats/contributors"
    response = requests.get(github_api)
    content = json.loads(response.text)
    avatar_urls = []

    for item in content:
        avatar_urls.append(item['author']['avatar_url'])
    return avatar_urls

def get_img_from_url(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img

def crop_avatar_into_circle(img: Image.Image):
    if img.format == 'PNG':
        img = img.convert('RGB')
        
    # Open the input image as numpy array, convert to RGB
    img_np = np.array(img)
    h, w = img.size

    # Create same size alpha layer with circle
    alpha = Image.new(mode='L', size=img.size, color=0)
    draw = ImageDraw.Draw(alpha)
    draw.pieslice([0, 0, h, w], 0, 360, fill=255)

    # Convert alpha Image to numpy array
    alpha_np = np.array(alpha)

    # Add alpha layer to RGB
    img_np = np.dstack((img_np, alpha_np))
    img = Image.fromarray(img_np)
    return img

def create_img_grid(img_list, num_cols, img_size, spacing=0):
    num_img = len(img_list)
    num_rows = math.ceil(num_img / num_cols)
    img_height = num_rows * img_size + spacing * max(0, num_rows - 1)
    img_width = num_cols * img_size + spacing * max(0, num_cols - 1)

    output_img = Image.new('RGBA', (img_width, img_height), (255, 0, 0, 0))

    index = 0
    for row in range(num_rows):
        for col in range(num_cols):
            img = img_list[index]
            img = img.resize((img_size, img_size))
            x_coordinate = col * (img_size + spacing)
            y_coordinate = row * (img_size + spacing)
            pos = (x_coordinate, y_coordinate)
            output_img.paste(img, pos)
            index += 1

            if index == len(img_list):
                break
    return output_img


def main():
    args = parse_args()
    avatar_urls = get_contributor_avatars(args.repo)
    random.shuffle(avatar_urls)
    avatar_imgs = [get_img_from_url(url) for url in avatar_urls]
    cropeed_avatar_imgs = [crop_avatar_into_circle(img) for img in avatar_imgs]


    output_img = create_img_grid(cropeed_avatar_imgs, num_cols=10, img_size=100, spacing=10)
    output_img.save(args.output)


if __name__ == '__main__':
    main()