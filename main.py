from flask import Flask, render_template, request, jsonify, Response
import requests
import re
import json
import os
import yt_dlp
from datetime import datetime

app = Flask(__name__)

# Your Cobalt instance URL
COBALT_API_URL = "https://genetic-britta-sjimenezn-80e305b4.koyeb.app/api/json"

# Simple cache for search results
search_cache = {}

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/search')
def search():
    """Search YouTube videos"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Check cache
    cache_key = query.lower()
    if cache_key in search_cache:
        cache_time, results = search_cache[cache_key]
        if (datetime.now() - cache_time).seconds < 300:  # 5 minute cache
            return jsonify({'videos': results})
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'playlistend': 15,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_url = f"ytsearch15:{query}"
            info = ydl.extract_info(search_url, download=False)
            entries = info.get('entries', [])
            results = []
            for entry in entries:
                results.append({
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'webpage_url': entry.get('webpage_url') or f"https://youtube.com/watch?v={entry.get('id')}",
                    'thumbnail': entry.get('thumbnail'),
                    'duration': entry.get('duration_string'),
                    'author': entry.get('uploader', 'Unknown')
                })
            
            search_cache[cache_key] = (datetime.now(), results)
            return jsonify({'videos': results})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/formats')
def get_formats():
    """Get available formats (standard quality options)"""
    url = request.args.get('url', '')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    # Extract video ID for thumbnail
    video_id = None
    if 'v=' in url:
        video_id = url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[1].split('?')[0]
    
    # Get video title
    video_title = "Video"
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Video')
    except:
        pass
    
    # Standard quality options
    qualities = [
        {'quality': '2160p', 'height': 2160},
        {'quality': '1440p', 'height': 1440},
        {'quality': '1080p', 'height': 1080},
        {'quality': '720p', 'height': 720},
        {'quality': '480p', 'height': 480},
        {'quality': '360p', 'height': 360},
        {'quality': '240p', 'height': 240},
        {'quality': '144p', 'height': 144}
    ]
    
    formats = []
    for q in qualities:
        formats.append({
            'format_id': str(q['height']),
            'quality': q['quality'],
            'height': q['height'],
            'has_audio': True,
            'ext': 'mp4'
        })
    
    thumbnail = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else ""
    
    return jsonify({
        'title': video_title,
        'thumbnail': thumbnail,
        'webpage_url': url,
        'formats': formats
    })

@app.route('/api/download')
def download():
    """Download video using Cobalt API"""
    url = request.args.get('url', '')
    quality = request.args.get('quality', '720p')
    format_id = request.args.get('format_id', '')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    # Extract quality number
    quality_num = 720
    if quality:
        quality_num = int(''.join(filter(str.isdigit, quality)))
    elif format_id:
        quality_num = int(''.join(filter(str.isdigit, format_id)))
    
    # Map to Cobalt's format
    quality_map = {
        2160: '2160',
        1440: '1440',
        1080: '1080',
        720: '720',
        480: '480',
        360: '360',
        240: '240',
        144: '144'
    }
    cobalt_quality = quality_map.get(quality_num, '720')
    
    payload = {
        'url': url,
        'vQuality': cobalt_quality,
        'vCodec': 'h264',
        'aFormat': 'mp3',
        'isAudioOnly': False,
        'filenamePattern': 'classic'
    }
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(COBALT_API_URL, json=payload, headers=headers, timeout=60)
        data = response.json()
        
        if data.get('status') == 'error':
            return jsonify({'error': data.get('text', 'Unknown error')}), 500
        
        if data.get('status') == 'success' or data.get('status') == 'redirect':
            download_url = data.get('url')
            
            if not download_url:
                return jsonify({'error': 'No download URL received'}), 500
            
            # Stream the file
            file_response = requests.get(download_url, stream=True, timeout=60)
            
            def generate():
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            # Get video ID for filename
            video_title = "video"
            video_id_match = re.search(r'v=([a-zA-Z0-9_-]+)', url)
            if video_id_match:
                video_title = f"youtube_{video_id_match.group(1)}"
            
            filename = f"{video_title}_{cobalt_quality}p.mp4"
            
            return Response(
                generate(),
                mimetype='video/mp4',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'video/mp4'
                }
            )
        else:
            return jsonify({'error': f'Unexpected response: {data}'}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
