FROM runpod/worker-comfyui:5.4.1-base

# install custom nodes using comfy-cli
RUN comfy-node-install comfyui-kjnodes gguf RES4LYF OneButtonPrompt rgthree-comfy
