import os
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
import webbrowser
from upload_utils import upload_image_to_gcs  # from your upload_utils.py

def generate_nightclub_page(json_file: str, output_html: str, bucket_name: str):
    # Load the scraped JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    # Limit total posts to 12
    posts = posts[:12]

    # Determine the Instagram username from the first post, if available.
    username = posts[0].get("ownerUsername") if posts and posts[0].get("ownerUsername") else "Instagram Account"

    # Process parent posts: upload the image and update the field "proxy_image"
    for post in posts:
        image_url = None
        if post.get("images") and len(post["images"]) > 0:
            image_url = post["images"][0]
        elif post.get("displayUrl"):
            image_url = post["displayUrl"]
        
        if image_url:
            dest_blob = f"images/{post.get('id', 'unknown')}.jpg"
            try:
                public_url = upload_image_to_gcs(image_url, bucket_name, dest_blob)
                post["proxy_image"] = public_url
            except Exception as e:
                print(f"Error uploading image for post {post.get('id')}: {e}")
                post["proxy_image"] = image_url  # Fallback to original URL if upload fails
        else:
            post["proxy_image"] = None

        # Process child posts (if any)
        if post.get("childPosts") and isinstance(post["childPosts"], list):
            for child in post["childPosts"]:
                child_image_url = None
                if child.get("images") and len(child["images"]) > 0:
                    child_image_url = child["images"][0]
                elif child.get("displayUrl"):
                    child_image_url = child["displayUrl"]
                if child_image_url:
                    child_dest_blob = f"images/{child.get('id', 'unknown')}.jpg"
                    try:
                        child_public_url = upload_image_to_gcs(child_image_url, bucket_name, child_dest_blob)
                        child["proxy_image"] = child_public_url
                    except Exception as e:
                        print(f"Error uploading image for child post {child.get('id')}: {e}")
                        child["proxy_image"] = child_image_url
                else:
                    child["proxy_image"] = None

    # Split posts into landing_posts (first 3) and gallery_posts (the rest)
    landing_posts = posts[:3]
    gallery_posts = posts[3:]

    # Set up the Jinja2 environment using your "templates" folder.
    env = Environment(
        loader=FileSystemLoader(searchpath="templates"),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("nightclub_template.html")

    # Render the template passing the username and both post lists.
    rendered_html = template.render(
        username=username,
        landing_posts=landing_posts,
        gallery_posts=gallery_posts
    )

    # Write the rendered HTML to the output file.
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    
    print("Nightclub HTML page generated:", output_html)
    webbrowser.open("file://" + os.path.realpath(output_html))

if __name__ == "__main__":
    # Example usage – update the JSON filename and your bucket name accordingly.
    generate_nightclub_page("static/scraped_data_example.json", "static/nightclub_output.html", "your-gcs-bucket-name")
