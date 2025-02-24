import os
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
import webbrowser
from upload_utils import upload_image_to_gcs

def unify_sidecars(posts):
    """
    Merge multiple items with the same shortCode into one parent + childPosts.
    """
    merged = {}

    for p in posts:
        sc = p.get("shortCode")
        if not sc:
            merged[p.get("id", "unknown_no_sc")] = p
            continue
        
        if sc not in merged:
            p.setdefault("childPosts", [])
            merged[sc] = p
        else:
            parent = merged[sc]
            parent.setdefault("childPosts", [])
            parent["childPosts"].append(p)

    return list(merged.values())


def process_images_for_post(post, bucket_name):
    """
    Upload the 'main' post image, then child posts if any.
    """
    # Upload main (parent) post image
    image_url = None
    if 'images' in post and post['images']:
        image_url = post['images'][0]
    elif 'displayUrl' in post and post['displayUrl']:
        image_url = post['displayUrl']
    
    if image_url:
        try:
            # Use post id to form a unique filename
            destination_blob = f"images/{post.get('id','unknown')}.jpg"
            public_url = upload_image_to_gcs(image_url, bucket_name, destination_blob)
            post['proxy_image'] = public_url
        except Exception as e:
            print(f"Error uploading parent image for post {post.get('id')}: {e}")
            # fallback to original
            post['proxy_image'] = image_url
    else:
        post['proxy_image'] = None

    # If this post has childPosts, upload each child
    if 'childPosts' in post and isinstance(post['childPosts'], list):
        for child in post['childPosts']:
            child_url = None
            if 'images' in child and child['images']:
                child_url = child['images'][0]
            elif 'displayUrl' in child and child['displayUrl']:
                child_url = child['displayUrl']
            
            if child_url:
                try:
                    child_dest_blob = f"images/{child.get('id','child_unknown')}.jpg"
                    public_url = upload_image_to_gcs(child_url, bucket_name, child_dest_blob)
                    child['proxy_image'] = public_url
                except Exception as ce:
                    print(f"Error uploading child image for post {child.get('id')}: {ce}")
                    child['proxy_image'] = child_url
            else:
                child['proxy_image'] = None


def generate_cms_page(json_file: str, output_html: str, bucket_name: str):
    # Load scraped JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        all_posts = json.load(f)

    # Step 1: unify sidecars => so each 'parent' has a 'childPosts' array
    posts_merged = unify_sidecars(all_posts)

    # (Optional) sort them by timestamp descending, if desired
    # If a post is missing 'timestamp', it might sort unpredictably
    posts_merged.sort(key=lambda p: p.get('timestamp',''), reverse=True)

    # Step 2: upload images for parent + child
    for post in posts_merged:
        process_images_for_post(post, bucket_name)

    # Step 3: Render using Jinja2
    env = Environment(
        loader=FileSystemLoader(searchpath="templates"),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("cms_template.html")
    rendered_html = template.render(posts=posts_merged)

    # Step 4: Write output HTML
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    print("CMS HTML page generated successfully:", output_html)
    webbrowser.open("file://" + os.path.realpath(output_html))

if __name__ == "__main__":
    # For local testing
    generate_cms_page("static/scraped_data_example.json", "static/cms_output.html", "your-bucket-name")
