import os
import pickle
import numpy as np
from scipy.signal import butter, filtfilt
import argparse
import json 


def get_raw_data(tags_to_load, data_tags_to_load, root_data_folder, timestamps = True, participant_dirs = False):
    flat_data = {}
    participants = []
    for t in tags_to_load:
        if participant_dirs:
            load_dir = f"{root_data_folder}/{t}/"
        else:
            load_dir = f"{root_data_folder}/{t}"
        if True:
            for f in data_tags_to_load:
                tag_found = False
                if f not in flat_data:
                    flat_data[f] = []
                # if os.path.exists(f"{load_dir}{f}"):
                #     temp = np.fromfile(f"{load_dir}{f}", dtype = float)
                #     tag_found = True
                if os.path.exists(f"{load_dir}{f}"):
                    temp = np.load(f"{load_dir}{f}", allow_pickle=True).astype(float)
                    print(f"{load_dir}{f}", len(temp))

                    tag_found = True
                if tag_found:
                    flat_data[f].extend(temp.tolist())
                else:
                    print(f"Tag {f} not found for participant {t}")

    return flat_data

def butter_filter(cutoff, fs, filter_direction, order=5):
    assert filter_direction == "low" or filter_direction == "high"
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff,
                         btype=filter_direction, analog=False)
    return b, a

def apply_butterworth_filter(data, cutoff, filter_direction, fs, order=5):
    b, a = butter_filter(cutoff, fs, filter_direction, order=order)
    y = filtfilt(b, a, data)
    return y



def main():
    # 1. Initialize the parser object
    parser = argparse.ArgumentParser(description="Reformat study data for annotation.")

    parser.add_argument("pid", type=str, help="Participant ID (required)")

    parser.add_argument("-c", "--config", type=str, default="./config_thomas.json", help="Configuration file (default: default_config)")

    args = parser.parse_args()

    config = json.load(open(args.config, "r"))
    
    p_data = get_raw_data([args.pid], config["channels_to_load"], config["data_path"], participant_dirs=True)

    n_channels = len(p_data.keys())
    n_samples = len(next(iter(p_data.values())))

    data = np.zeros((n_samples, n_channels+1))
    timestamps = np.arange(n_samples) / config["sample_rate"]

    data[:, 0] = timestamps

    for channel, (key, signal) in enumerate(p_data.items()):
        signal = np.array(signal)
        signal = apply_butterworth_filter(signal, cutoff=100, filter_direction="high", fs=config["sample_rate"], order=4)
        data[:, channel+1] = signal
        print(data[:, channel+1].shape, np.max(data[:, channel+1]), np.min(data[:, channel+1]))

    if not os.path.exists(config["data_save_loc"]):
        os.makedirs(config["data_save_loc"])


    np.save(f"{config['data_save_loc']}/{args.pid}_{config['sample_rate']}.npy", data)


    if os.path.exists(f"{config['voice_annots_path']}/{args.pid}_speech_timestamps.pkl"):
        voice_annots = pickle.load(open(f"{config['voice_annots_path']}/{args.pid}_speech_timestamps.pkl", "rb"))
    
    elif os.path.exists(f"{config['voice_annots_path']}/rp{args.pid}_speech_timestamps.pkl"):
        voice_annots = pickle.load(open(f"{config['voice_annots_path']}/rp{args.pid}_speech_timestamps.pkl", "rb"))
    
    else:
        print(f"Voice annotations not found for participant {args.pid}")
        print(f"{config['voice_annots_path']}/rp{args.pid}_speech_timestamps.pkl")
        voice_annots = []
    
    voice_annots_json = []
    for v in voice_annots:
        a = {
            "label": "Voice",
            "start_time": v["start"]/config["annot_sample_rate"],
            "end_time": v["end"]/config["annot_sample_rate"],
            "duration": (v["end"]-v["start"])/config["annot_sample_rate"],
            "color": [
                255,
                0,
                0
            ],
          "notes": ""
        }
        voice_annots_json.append(a)
    json_out = {
        "sensor_file": f"{args.pid}_{config['sample_rate']}.npy",
        "annotation_count": len(voice_annots_json),
        "annotations": voice_annots_json
    }
    with open(f"{config['data_save_loc']}/{args.pid}_annotations.json", "w") as f:
        json.dump(json_out, f, indent=2)

if __name__ == "__main__":
    main()