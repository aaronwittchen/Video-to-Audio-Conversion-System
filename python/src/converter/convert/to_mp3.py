import pika, json, tempfile, os
from bson.objectid import ObjectId
import ffmpeg

def start(message, fs_videos, fs_mp3s, channel):
    message = json.loads(message)

    # Create temp file for video (keep it similar to your original structure)
    tf = tempfile.NamedTemporaryFile(delete=False)
    # video contents
    out = fs_videos.get(ObjectId(message["video_fid"]))
    # add video contents to empty file
    tf.write(out.read())
    tf.flush()  # Make sure data is written to disk
    tf_name = tf.name
    tf.close()

    try:
        # write audio to the file using ffmpeg instead of moviepy
        tf_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
        
        # Use ffmpeg to extract audio and convert to MP3
        (
            ffmpeg
            .input(tf_name)
            .output(tf_path, acodec='mp3', audio_bitrate='192k')
            .overwrite_output()
            .run(quiet=True, capture_stdout=True, capture_stderr=True)
        )

        # save file to mongo (keeping your original structure)
        f = open(tf_path, "rb")
        data = f.read()
        fid = fs_mp3s.put(data)
        f.close()
        os.remove(tf_path)

        message["mp3_fid"] = str(fid)

        try:
            channel.basic_publish(
                exchange="",
                routing_key=os.environ.get("MP3_QUEUE"),
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                ),
            )
        except Exception as err:
            fs_mp3s.delete(fid)
            return "failed to publish message"
            
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"FFmpeg conversion error: {error_msg}")
        return f"failed to convert video: {error_msg}"
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        return f"failed to process video: {str(e)}"
    finally:
        # Clean up the temp video file
        if os.path.exists(tf_name):
            os.remove(tf_name)