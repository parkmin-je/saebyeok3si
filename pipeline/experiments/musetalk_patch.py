"""MuseTalk 얼굴 랜드마크를 DWPose(mmpose, 설치 까다로움) 대신 face_alignment 68점으로 바꾸는 패치.

python pipeline/experiments/musetalk_patch.py /tmp/MuseTalk
"""
import sys
from pathlib import Path

p = Path(sys.argv[1]) / "musetalk/utils/preprocessing.py"
s = p.read_text()
s = s.replace("from mmpose.apis import inference_topdown, init_model\nfrom mmpose.structures import merge_data_samples\n",
              "import face_alignment as _fa_pip\n")
s = s.replace("config_file = './musetalk/utils/dwpose/rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py'\n"
              "checkpoint_file = './models/dwpose/dw-ll_ucoco_384.pth'\n"
              "model = init_model(config_file, checkpoint_file, device=device)\n",
              "_lm = _fa_pip.FaceAlignment(_fa_pip.LandmarksType.TWO_D, flip_input=False, device=str(device))\n")
s = s.replace("        results = inference_topdown(model, np.asarray(fb)[0])\n"
              "        results = merge_data_samples(results)\n"
              "        keypoints = results.pred_instances.keypoints\n"
              "        face_land_mark= keypoints[0][23:91]\n",
              "        _l = _lm.get_landmarks(np.asarray(fb)[0][:, :, ::-1].copy())\n"
              "        if not _l:\n"
              "            coords_list += [coord_placeholder]\n"
              "            continue\n"
              "        face_land_mark = _l[0]\n")
assert "mmpose.apis" not in s and "_lm.get_landmarks" in s, "패치 실패"
p.write_text(s)
print("patched", p)
