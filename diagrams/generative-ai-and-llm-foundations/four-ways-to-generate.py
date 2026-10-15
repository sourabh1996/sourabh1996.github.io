# The four main families of generative models, each drawn as the path from "nothing" to new content.
SPEC = {
    "title": "Four ways a model can generate something new",
    "accent": "purple",
    "width": 1100, "height": 860,
    "bands": [
        {"y": 80, "h": 175, "label": "Auto-\nregressive", "color": "blue", "tile": 135},
        {"y": 270, "h": 175, "label": "Diffusion", "color": "teal", "tile": 135},
        {"y": 460, "h": 190, "label": "GAN", "color": "coral", "tile": 135},
        {"y": 665, "h": 175, "label": "VAE", "color": "amber", "tile": 135},
    ],
    "nodes": {
        # Autoregressive
        "ar_in": {"x": 175, "y": 120, "w": 160, "h": 90, "icon": "💬", "label": "Text so far", "sub": "\"one cutting\"", "color": "blue"},
        "ar_model": {"x": 380, "y": 110, "w": 210, "h": 110, "icon": "🧠", "label": "Predict next piece", "sub": "chai 62% · coffee 21%\nsamosa 9% · ...", "color": "blue"},
        "ar_pick": {"x": 640, "y": 120, "w": 150, "h": 90, "icon": "🎲", "label": "Pick one", "sub": "\"chai\"", "color": "blue"},
        "ar_out": {"x": 860, "y": 120, "w": 200, "h": 90, "icon": "📝", "label": "Text, code", "sub": "LLMs work this way", "color": "blue"},
        # Diffusion
        "df_noise": {"x": 175, "y": 310, "w": 160, "h": 95, "icon": "🌫️", "label": "Pure noise", "sub": "random static", "color": "teal"},
        "df_step": {"x": 400, "y": 300, "w": 230, "h": 115, "icon": "🧽", "label": "Remove a little noise", "sub": "guided by the prompt\n🔁 repeat 20 to 1000 times", "color": "teal"},
        "df_out": {"x": 860, "y": 310, "w": 200, "h": 95, "icon": "🖼️", "label": "Clean image", "sub": "image, video, audio", "color": "teal"},
        # GAN
        "gan_seed": {"x": 175, "y": 500, "w": 140, "h": 90, "icon": "🎲", "label": "Random seed", "color": "coral"},
        "gan_gen": {"x": 360, "y": 500, "w": 170, "h": 90, "icon": "🎨", "label": "Generator", "sub": "the forger", "color": "coral"},
        "gan_fake": {"x": 580, "y": 500, "w": 140, "h": 90, "icon": "🖼️", "label": "Fake", "color": "coral"},
        "gan_disc": {"x": 770, "y": 490, "w": 180, "h": 110, "icon": "🕵️", "label": "Discriminator", "sub": "the inspector:\nreal or fake?", "color": "coral"},
        "gan_real": {"x": 975, "y": 500, "w": 90, "h": 90, "icon": "📷", "label": "Real", "color": "gray"},
        # VAE
        "vae_in": {"x": 175, "y": 705, "w": 130, "h": 95, "icon": "🖼️", "label": "Image", "color": "amber"},
        "vae_enc": {"x": 340, "y": 705, "w": 150, "h": 95, "icon": "🗜️", "label": "Encoder", "sub": "squeeze", "color": "amber"},
        "vae_code": {"x": 530, "y": 705, "w": 170, "h": 95, "icon": "🔢", "label": "Small code", "sub": "a few numbers\n(the latent space)", "color": "amber"},
        "vae_dec": {"x": 740, "y": 705, "w": 150, "h": 95, "icon": "🧩", "label": "Decoder", "sub": "rebuild", "color": "amber"},
        "vae_out": {"x": 930, "y": 705, "w": 140, "h": 95, "icon": "✨", "label": "New image", "color": "amber"},
    },
    "edges": [
        {"from": "ar_in", "to": "ar_model"},
        {"from": "ar_model", "to": "ar_pick"},
        {"from": "ar_pick", "to": "ar_out", "label": "until done"},
        {"from": "ar_pick", "to": "ar_in", "label": "append the piece and repeat", "from_side": "bottom", "to_side": "bottom", "via": [(715, 238), (245, 238)], "label_at": (480, 240)},
        {"from": "df_noise", "to": "df_step"},
        {"from": "df_step", "to": "df_out", "label": "after the last step", "label_at": (745, 348)},
        {"from": "gan_seed", "to": "gan_gen"},
        {"from": "gan_gen", "to": "gan_fake"},
        {"from": "gan_fake", "to": "gan_disc"},
        {"from": "gan_real", "to": "gan_disc"},
        {"from": "gan_disc", "to": "gan_gen", "label": "\"I caught you\" → forger improves", "from_side": "bottom", "to_side": "bottom", "via": [(870, 625), (445, 625)], "label_at": (655, 628)},
        {"from": "vae_in", "to": "vae_enc"},
        {"from": "vae_enc", "to": "vae_code"},
        {"from": "vae_code", "to": "vae_dec"},
        {"from": "vae_dec", "to": "vae_out"},
    ],
    "notes": [
        {"x": 615, "y": 825, "text": "To create: skip the encoder, pick a new code, decode it"},
    ],
}
