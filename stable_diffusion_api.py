#!/usr/bin/env python3
"""
Stable Diffusion WebUI API Client
Provides easy access to Stable Diffusion WebUI API endpoints.
Based on API documentation from API.md
"""

import base64
import json
from typing import Dict, List, Optional, Union, Any
import requests
from requests.auth import HTTPBasicAuth


class StableDiffusionAPI:
    """Client for Stable Diffusion WebUI API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:7860", 
                 username: Optional[str] = None, 
                 password: Optional[str] = None):
        """
        Initialize the Stable Diffusion API client.
        
        Args:
            base_url: Base URL of the API (e.g., "http://127.0.0.1:7860")
            username: Username for HTTP Basic Auth (if enabled)
            password: Password for HTTP Basic Auth (if enabled)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Set up authentication if provided
        if username and password:
            self.session.auth = HTTPBasicAuth(username, password)
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, 
                     json_data: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/sdapi/v1/txt2img")
            json_data: JSON data to send in request body
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.exceptions.RequestException: For HTTP errors
            ValueError: For invalid responses
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                timeout=300  # 5 minute timeout for image generation
            )
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {}
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Try to extract error details from response if available
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_info = e.response.json()
                    error_detail = error_info.get('detail', str(e))
                except:
                    error_detail = e.response.text or str(e)
            raise requests.exceptions.RequestException(f"API request failed: {error_detail}")
    
    # ====================== TEXT-TO-IMAGE ======================
    
    def txt2img(self, prompt: str, 
                negative_prompt: str = "",
                seed: int = -1,
                steps: int = 20,
                cfg_scale: float = 7.0,
                width: int = 512,
                height: int = 512,
                sampler_name: str = "Euler",
                batch_size: int = 1,
                n_iter: int = 1,
                restore_faces: bool = False,
                tiling: bool = False,
                do_not_save_samples: bool = False,
                do_not_save_grid: bool = False,
                eta: Optional[float] = None,
                s_min_uncond: Optional[float] = None,
                s_churn: Optional[float] = None,
                s_tmax: Optional[float] = None,
                s_tmin: Optional[float] = None,
                s_noise: Optional[float] = None,
                override_settings: Optional[Dict] = None,
                override_settings_restore_afterwards: bool = True,
                script_name: Optional[str] = None,
                script_args: Optional[List] = None,
                send_images: bool = True,
                save_images: bool = False,
                alwayson_scripts: Optional[Dict] = None,
                force_task_id: Optional[str] = None,
                infotext: Optional[str] = None,
                styles: Optional[List[str]] = None,
                subseed: int = -1,
                subseed_strength: float = 0.0,
                seed_resize_from_h: int = -1,
                seed_resize_from_w: int = -1,
                scheduler: Optional[str] = None,
                denoising_strength: Optional[float] = None) -> Dict:
        """
        Generate images from text prompt.
        
        POST /sdapi/v1/txt2img
        
        Args:
            prompt: Positive prompt
            negative_prompt: Negative prompt
            seed: Seed (-1 for random)
            steps: Number of sampling steps
            cfg_scale: CFG scale
            width: Image width
            height: Image height
            sampler_name: Sampler name
            batch_size: Images per batch
            n_iter: Number of iterations
            restore_faces: Whether to restore faces
            tiling: Enable tiling
            do_not_save_samples: Don't save samples
            do_not_save_grid: Don't save grid
            eta: ETA value
            s_min_uncond: Minimum CFG unconditional guidance
            s_churn: S-Churn parameter
            s_tmax: S-Tmax parameter
            s_tmin: S-Tmin parameter
            s_noise: S-Noise parameter
            override_settings: Settings to override
            override_settings_restore_afterwards: Restore settings after
            script_name: Script name to run
            script_args: Script arguments
            send_images: Return images in response
            save_images: Save images to disk
            alwayson_scripts: Always-on scripts
            force_task_id: Force task ID
            infotext: Infotext to parse
            styles: Style names to apply
            subseed: Variation seed
            subseed_strength: Variation strength
            seed_resize_from_h: Resize from height
            seed_resize_from_w: Resize from width
            scheduler: Scheduler name
            denoising_strength: Denoising strength
            
        Returns:
            Dictionary with images (base64), parameters, and info
        """
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height,
            "sampler_name": sampler_name,
            "batch_size": batch_size,
            "n_iter": n_iter,
            "restore_faces": restore_faces,
            "tiling": tiling,
            "do_not_save_samples": do_not_save_samples,
            "do_not_save_grid": do_not_save_grid,
            "send_images": send_images,
            "save_images": save_images,
        }
        
        # Add optional parameters if provided
        optional_params = {
            "eta": eta,
            "s_min_uncond": s_min_uncond,
            "s_churn": s_churn,
            "s_tmax": s_tmax,
            "s_tmin": s_tmin,
            "s_noise": s_noise,
            "override_settings": override_settings,
            "override_settings_restore_afterwards": override_settings_restore_afterwards,
            "script_name": script_name,
            "script_args": script_args,
            "send_images": send_images,
            "save_images": save_images,
            "alwayson_scripts": alwayson_scripts or {},
            "force_task_id": force_task_id,
            "infotext": infotext,
            "styles": styles,
            "subseed": subseed,
            "subseed_strength": subseed_strength,
            "seed_resize_from_h": seed_resize_from_h,
            "seed_resize_from_w": seed_resize_from_w,
            "scheduler": scheduler,
            "denoising_strength": denoising_strength,
        }
        
        # Filter out None values
        for key, value in optional_params.items():
            if value is not None:
                payload[key] = value
                
        return self._make_request("POST", "/sdapi/v1/txt2img", json_data=payload)
    
    # ====================== IMAGE-TO-IMAGE ======================
    
    def img2img(self, init_images: List[str],
                prompt: str = "",
                negative_prompt: str = "",
                seed: int = -1,
                steps: int = 50,
                cfg_scale: float = 7.0,
                width: int = 512,
                height: int = 512,
                sampler_name: str = "Euler",
                batch_size: int = 1,
                n_iter: int = 1,
                restore_faces: bool = False,
                tiling: bool = False,
                denoising_strength: float = 0.75,
                resize_mode: int = 0,
                image_cfg_scale: Optional[float] = None,
                mask: Optional[str] = None,
                mask_blur: Optional[int] = None,
                inpainting_fill: Optional[int] = None,
                inpaint_full_res: Optional[bool] = None,
                inpaint_full_res_padding: Optional[int] = None,
                inpainting_mask_invert: Optional[int] = None,
                initial_noise_multiplier: Optional[float] = None,
                script_name: Optional[str] = None,
                script_args: Optional[List] = None,
                send_images: bool = True,
                save_images: bool = False,
                alwayson_scripts: Optional[Dict] = None,
                include_init_images: bool = False,
                force_task_id: Optional[str] = None,
                infotext: Optional[str] = None,
                styles: Optional[List[str]] = None,
                subseed: int = -1,
                subseed_strength: float = 0.0,
                eta: Optional[float] = None) -> Dict:
        """
        Generate images from input images.
        
        POST /sdapi/v1/img2img
        
        Args:
            init_images: List of base64 encoded input images
            prompt: Positive prompt
            negative_prompt: Negative prompt
            seed: Seed (-1 for random)
            steps: Number of sampling steps
            cfg_scale: CFG scale
            width: Image width
            height: Image height
            sampler_name: Sampler name
            batch_size: Batch size
            n_iter: Number of iterations
            restore_faces: Whether to restore faces
            tiling: Enable tiling
            denoising_strength: Denoising strength (0-1)
            resize_mode: Resize mode (0=resize, 1=crop)
            image_cfg_scale: Image CFG scale
            mask: Base64 encoded mask image
            mask_blur: Mask blur
            inpainting_fill: Inpainting fill
            inpaint_full_res: Full resolution inpaint
            inpaint_full_res_padding: Inpaint padding
            inpainting_mask_invert: Mask invert
            initial_noise_multiplier: Initial noise multiplier
            script_name: Script name to run
            script_args: Script arguments
            send_images: Return images in response
            save_images: Save images to disk
            alwayson_scripts: Always-on scripts
            include_init_images: Include init images in response
            force_task_id: Force task ID
            infotext: Infotext to parse
            styles: Style names to apply
            subseed: Variation seed
            subseed_strength: Variation strength
            eta: ETA value
            
        Returns:
            Dictionary with images (base64), parameters, and info
        """
        payload = {
            "init_images": init_images,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height,
            "sampler_name": sampler_name,
            "batch_size": batch_size,
            "n_iter": n_iter,
            "restore_faces": restore_faces,
            "tiling": tiling,
            "denoising_strength": denoising_strength,
            "resize_mode": resize_mode,
            "send_images": send_images,
            "save_images": save_images,
        }
        
        # Add optional parameters if provided
        optional_params = {
            "image_cfg_scale": image_cfg_scale,
            "mask": mask,
            "mask_blur": mask_blur,
            "inpainting_fill": inpainting_fill,
            "inpaint_full_res": inpaint_full_res,
            "inpaint_full_res_padding": inpaint_full_res_padding,
            "inpainting_mask_invert": inpainting_mask_invert,
            "initial_noise_multiplier": initial_noise_multiplier,
            "script_name": script_name,
            "script_args": script_args,
            "alwayson_scripts": alwayson_scripts or {},
            "include_init_images": include_init_images,
            "force_task_id": force_task_id,
            "infotext": infotext,
            "styles": styles,
            "subseed": subseed,
            "subseed_strength": subseed_strength,
            "eta": eta,
        }
        
        # Filter out None values
        for key, value in optional_params.items():
            if value is not None:
                payload[key] = value
                
        return self._make_request("POST", "/sdapi/v1/img2img", json_data=payload)
    
    # ====================== EXTRA SINGLE IMAGE ======================
    
    def extra_single_image(self, image: str,
                           resize_mode: int = 0,
                           show_extras_results: bool = True,
                           gfpgan_visibility: float = 0.0,
                           codeformer_visibility: float = 0.0,
                           codeformer_weight: float = 0.0,
                           upscaling_resize: float = 2.0,
                           upscaling_resize_w: int = 512,
                           upscaling_resize_h: int = 512,
                           upscaling_crop: bool = True,
                           upscaler_1: str = "None",
                           upscaler_2: str = "None",
                           extras_upscaler_2_visibility: float = 0.0,
                           upscale_first: bool = False) -> Dict:
        """
        Upscale or enhance a single image.
        
        POST /sdapi/v1/extra-single-image
        
        Args:
            image: Base64 encoded input image
            resize_mode: 0=upscale by factor, 1=upscale to size
            show_extras_results: Return processed image
            gfpgan_visibility: GFPGAN face restoration strength (0-1)
            codeformer_visibility: CodeFormer visibility (0-1)
            codeformer_weight: CodeFormer weight (0-1)
            upscaling_resize: Upscale factor (for mode 0)
            upscaling_resize_w: Target width (for mode 1)
            upscaling_resize_h: Target height (for mode 1)
            upscaling_crop: Crop to fit
            upscaler_1: Primary upscaler
            upscaler_2: Secondary upscaler
            extras_upscaler_2_visibility: Secondary upscaler visibility (0-1)
            upscale_first: Upscale before face restore
            
        Returns:
            Dictionary with image (base64) and html_info
        """
        payload = {
            "image": image,
            "resize_mode": resize_mode,
            "show_extras_results": show_extras_results,
            "gfpgan_visibility": gfpgan_visibility,
            "codeformer_visibility": codeformer_visibility,
            "codeformer_weight": codeformer_weight,
            "upscaling_resize": upscaling_resize,
            "upscaling_resize_w": upscaling_resize_w,
            "upscaling_resize_h": upscaling_resize_h,
            "upscaling_crop": upscaling_crop,
            "upscaler_1": upscaler_1,
            "upscaler_2": upscaler_2,
            "extras_upscaler_2_visibility": extras_upscaler_2_visibility,
            "upscale_first": upscale_first,
        }
        
        return self._make_request("POST", "/sdapi/v1/extra-single-image", json_data=payload)
    
    # ====================== PNG INFO ======================
    
    def png_info(self, image: str) -> Dict:
        """
        Extract metadata from a PNG image.
        
        POST /sdapi/v1/png-info
        
        Args:
            image: Base64 encoded PNG image
            
        Returns:
            Dictionary with info, items, and parameters
        """
        payload = {"image": image}
        return self._make_request("POST", "/sdapi/v1/png-info", json_data=payload)
    
    # ====================== PROGRESS TRACKING ======================
    
    def progress(self, skip_current_image: bool = False) -> Dict:
        """
        Get current generation progress.
        
        GET /sdapi/v1/progress
        
        Args:
            skip_current_image: Skip returning current image
            
        Returns:
            Dictionary with progress, eta_relative, state, current_image, textinfo
        """
        params = {"skip_current_image": skip_current_image}
        return self._make_request("GET", "/sdapi/v1/progress", params=params)
    
    # ====================== CONTROL ENDPOINTS ======================
    
    def interrupt(self) -> Dict:
        """
        Stop the current generation.
        
        POST /sdapi/v1/interrupt
        
        Returns:
            Empty dictionary
        """
        return self._make_request("POST", "/sdapi/v1/interrupt")
    
    def skip(self) -> Dict:
        """
        Skip the current generation step.
        
        POST /sdapi/v1/skip
        
        Returns:
            Empty dictionary (204 No Content)
        """
        return self._make_request("POST", "/sdapi/v1/skip")
    
    def unload_checkpoint(self) -> Dict:
        """
        Unload the current model from GPU memory.
        
        POST /sdapi/v1/unload-checkpoint
        
        Returns:
            Empty dictionary
        """
        return self._make_request("POST", "/sdapi/v1/unload-checkpoint")
    
    def reload_checkpoint(self) -> Dict:
        """
        Reload the checkpoint to GPU.
        
        POST /sdapi/v1/reload-checkpoint
        
        Returns:
            Empty dictionary
        """
        return self._make_request("POST", "/sdapi/v1/reload-checkpoint")
    
    # ====================== OPTIONS MANAGEMENT ======================
    
    def get_options(self) -> Dict:
        """
        Get all webui options.
        
        GET /sdapi/v1/options
        
        Returns:
            JSON object with all options
        """
        return self._make_request("GET", "/sdapi/v1/options")
    
    def set_options(self, options: Dict) -> Dict:
        """
        Set webui options.
        
        POST /sdapi/v1/options
        
        Args:
            options: Dictionary of option key-value pairs
            
        Returns:
            Empty dictionary (204 No Content)
        """
        return self._make_request("POST", "/sdapi/v1/options", json_data=options)
    
    # ====================== SYSTEM INFORMATION ======================
    
    def get_cmd_flags(self) -> Dict:
        """
        Get command line flags used to start the server.
        
        GET /sdapi/v1/cmd-flags
        
        Returns:
            Dictionary with cmd flags
        """
        return self._make_request("GET", "/sdapi/v1/cmd-flags")
    
    def get_samplers(self) -> List[Dict]:
        """
        Get list of available samplers.
        
        GET /sdapi/v1/samplers
        
        Returns:
            List of sampler dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/samplers")
    
    def get_schedulers(self) -> List[Dict]:
        """
        Get list of available schedulers.
        
        GET /sdapi/v1/schedulers
        
        Returns:
            List of scheduler dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/schedulers")
    
    def get_upscalers(self) -> List[Dict]:
        """
        Get list of available upscalers.
        
        GET /sdapi/v1/upscalers
        
        Returns:
            List of upscaler dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/upscalers")
    
    def get_sd_models(self) -> List[Dict]:
        """
        Get list of available Stable Diffusion checkpoints.
        
        GET /sdapi/v1/sd-models
        
        Returns:
            List of model dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/sd-models")
    
    def get_vae(self) -> List[Dict]:
        """
        Get list of available VAEs.
        
        GET /sdapi/v1/sd-vae
        
        Returns:
            List of VAE dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/sd-vae")
    
    def get_hypernetworks(self) -> List[Dict]:
        """
        Get list of available hypernetworks.
        
        GET /sdapi/v1/hypernetworks
        
        Returns:
            List of hypernetwork dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/hypernetworks")
    
    def get_face_restorers(self) -> List[Dict]:
        """
        Get list of face restoration models.
        
        GET /sdapi/v1/face-restorers
        
        Returns:
            List of face restorer dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/face-restorers")
    
    def get_realesrgan_models(self) -> List[Dict]:
        """
        Get list of Real-ESRGAN models.
        
        GET /sdapi/v1/realesrgan-models
        
        Returns:
            List of realesrgan model dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/realesrgan-models")
    
    def get_prompt_styles(self) -> List[Dict]:
        """
        Get list of prompt styles.
        
        GET /sdapi/v1/prompt-styles
        
        Returns:
            List of prompt style dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/prompt-styles")
    
    # ====================== EMBEDDINGS AND TRAINING ======================
    
    def get_embeddings(self) -> Dict:
        """
        Get loaded textual inversion embeddings.
        
        GET /sdapi/v1/embeddings
        
        Returns:
            Dictionary with loaded and skipped embeddings
        """
        return self._make_request("GET", "/sdapi/v1/embeddings")
    
    def refresh_embeddings(self) -> Dict:
        """
        Reload embeddings from disk.
        
        POST /sdapi/v1/refresh-embeddings
        
        Returns:
            Empty dictionary
        """
        return self._make_request("POST", "/sdapi/v1/refresh-embeddings")
    
    def refresh_checkpoints(self) -> Dict:
        """
        Reload checkpoints from disk.
        
        POST /sdapi/v1/refresh-checkpoints
        
        Returns:
            Empty dictionary
        """
        return self._make_request("POST", "/sdapi/v1/refresh-checkpoints")
    
    def refresh_vae(self) -> Dict:
        """
        Reload VAEs from disk.
        
        POST /sdapi/v1/refresh-vae
        
        Returns:
            Empty dictionary
        """
        return self._make_request("POST", "/sdapi/v1/refresh-vae")
    
    def create_embedding(self, name: str, init_text: str = "concept",
                         vectors: int = 1, overwrite: bool = False) -> Dict:
        """
        Create a new textual inversion embedding.
        
        POST /sdapi/v1/create/embedding
        
        Args:
            name: Embedding name
            init_text: Initial text
            vectors: Number of vectors
            overwrite: Whether to overwrite existing
            
        Returns:
            Dictionary with info message
        """
        payload = {
            "name": name,
            "init_text": init_text,
            "vectors": vectors,
            "overwrite": overwrite,
        }
        return self._make_request("POST", "/sdapi/v1/create/embedding", json_data=payload)
    
    def train_embedding(self, embedding_name: str, learn_rate: float = 0.005,
                        batch_size: int = 1, gradient_step: int = 1,
                        data_root: str = "dataset", log_directory: str = "logs",
                        training_width: int = 512, training_height: int = 512,
                        steps: int = 1000, clip_grad_mode: str = "disabled",
                        clip_grad_value: float = 0.1, shuffle_tags: bool = False,
                        tag_drop_out: int = 0, latent_sampling_method: str = "once",
                        alternating_bw: bool = False, save_embedding_every: int = 100,
                        save_image_with_stored_embedding: bool = True,
                        preview_from_tab: bool = False, preview_prompt: str = "",
                        preview_negative_prompt: str = "", preview_steps: int = 20,
                        preview_sampler: str = "Euler", preview_cfg_scale: float = 7.0,
                        preview_seed: int = 42, preview_width: int = 512,
                        preview_height: int = 512) -> Dict:
        """
        Train a textual inversion embedding.
        
        POST /sdapi/v1/train/embedding
        
        Args:
            embedding_name: Name of the embedding
            learn_rate: Learning rate
            batch_size: Batch size
            gradient_step: Gradient step
            data_root: Data root directory
            log_directory: Log directory
            training_width: Training width
            training_height: Training height
            steps: Training steps
            clip_grad_mode: Clip gradient mode
            clip_grad_value: Clip gradient value
            shuffle_tags: Shuffle tags
            tag_drop_out: Tag drop out
            latent_sampling_method: Latent sampling method
            alternating_bw: Alternating between width and height
            save_embedding_every: Save embedding every N steps
            save_image_with_stored_embedding: Save image with stored embedding
            preview_from_tab: Preview from tab
            preview_prompt: Preview prompt
            preview_negative_prompt: Preview negative prompt
            preview_steps: Preview steps
            preview_sampler: Preview sampler
            preview_cfg_scale: Preview CFG scale
            preview_seed: Preview seed
            preview_width: Preview width
            preview_height: Preview height
            
        Returns:
            Dictionary with training info
        """
        payload = {
            "embedding_name": embedding_name,
            "learn_rate": learn_rate,
            "batch_size": batch_size,
            "gradient_step": gradient_step,
            "data_root": data_root,
            "log_directory": log_directory,
            "training_width": training_width,
            "training_height": training_height,
            "steps": steps,
            "clip_grad_mode": clip_grad_mode,
            "clip_grad_value": clip_grad_value,
            "shuffle_tags": shuffle_tags,
            "tag_drop_out": tag_drop_out,
            "latent_sampling_method": latent_sampling_method,
            "alternating_bw": alternating_bw,
            "save_embedding_every": save_embedding_every,
            "save_image_with_stored_embedding": save_image_with_stored_embedding,
            "preview_from_tab": preview_from_tab,
            "preview_prompt": preview_prompt,
            "preview_negative_prompt": preview_negative_prompt,
            "preview_steps": preview_steps,
            "preview_sampler": preview_sampler,
            "preview_cfg_scale": preview_cfg_scale,
            "preview_seed": preview_seed,
            "preview_width": preview_width,
            "preview_height": preview_height,
        }
        return self._make_request("POST", "/sdapi/v1/train/embedding", json_data=payload)
    
    # ====================== MEMORY MANAGEMENT ======================
    
    def get_memory(self) -> Dict:
        """
        Get current memory usage information.
        
        GET /sdapi/v1/memory
        
        Returns:
            Dictionary with RAM and CUDA memory info
        """
        return self._make_request("GET", "/sdapi/v1/memory")
    
    # ====================== SCRIPTS ======================
    
    def get_scripts(self) -> Dict:
        """
        Get list of available scripts for txt2img and img2img.
        
        GET /sdapi/v1/scripts
        
        Returns:
            Dictionary with txt2img and img2img script lists
        """
        return self._make_request("GET", "/sdapi/v1/scripts")
    
    def get_script_info(self) -> List[Dict]:
        """
        Get detailed information about scripts and their parameters.
        
        GET /sdapi/v1/script-info
        
        Returns:
            List of script information dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/script-info")
    
    # ====================== EXTENSIONS ======================
    
    def get_extensions(self) -> List[Dict]:
        """
        Get list of installed extensions.
        
        GET /sdapi/v1/extensions
        
        Returns:
            List of extension dictionaries
        """
        return self._make_request("GET", "/sdapi/v1/extensions")
    
    # ====================== SERVER CONTROL ======================
    
    def server_stop(self) -> Dict:
        """
        Stop the webui server gracefully.
        Requires --api-server-stop flag.
        
        POST /sdapi/v1/server-stop
        
        Returns:
            Dictionary with status message
        """
        return self._make_request("POST", "/sdapi/v1/server-stop")
    
    def server_restart(self) -> Dict:
        """
        Restart the webui server.
        Requires --api-server-stop flag.
        
        POST /sdapi/v1/server-restart
        
        Returns:
            Empty dictionary (501 Not Implemented) if not restartable
        """
        return self._make_request("POST", "/sdapi/v1/server-restart")
    
    def server_kill(self) -> Dict:
        """
        Immediately kill the webui process.
        Requires --api-server-stop flag.
        
        POST /sdapi/v1/server-kill
        
        Returns:
            No response (process terminates)
        """
        return self._make_request("POST", "/sdapi/v1/server-kill")
    
    # ====================== INTERNAL ENDPOINTS ======================
    
    def ping(self) -> Dict:
        """
        Health check endpoint.
        
        GET /internal/ping
        
        Returns:
            Empty dictionary
        """
        return self._make_request("GET", "/internal/ping")
    
    def get_quicksettings_hint(self) -> List[Dict]:
        """
        Get quicksettings information.
        
        GET /internal/quicksettings-hint
        
        Returns:
            List of quicksettings dictionaries
        """
        return self._make_request("GET", "/internal/quicksettings-hint")
    
    def get_progress_detailed(self, id_task: Optional[str] = None,
                              id_live_preview: int = -1,
                              live_preview: bool = True) -> Dict:
        """
        Alternative progress endpoint with more details.
        
        GET /internal/progress
        
        Args:
            id_task: Task ID
            id_live_preview: Last preview ID
            live_preview: Include preview
            
        Returns:
            Dictionary with active, queued, completed progress info
        """
        params = {}
        if id_task is not None:
            params["id_task"] = id_task
        if id_live_preview != -1:
            params["id_live_preview"] = id_live_preview
        params["live_preview"] = live_preview
        
        return self._make_request("GET", "/internal/progress", params=params)
    
    def get_pending_tasks(self) -> Dict:
        """
        Get pending task count.
        
        GET /internal/pending-tasks
        
        Returns:
            Dictionary with size and tasks list
        """
        return self._make_request("GET", "/internal/pending-tasks")
    
    def get_profile_startup(self) -> Dict:
        """
        Get startup timing information.
        
        GET /internal/profile-startup
        
        Returns:
            Dictionary with startup timing info
        """
        return self._make_request("GET", "/internal/profile-startup")
    
    def get_sysinfo(self) -> Dict:
        """
        Get system information.
        
        GET /internal/sysinfo
        
        Returns:
            JSON text with system details
        """
        return self._make_request("GET", "/internal/sysinfo")
    
    # ====================== UTILITY METHODS ======================
    
    @staticmethod
    def encode_image_to_base64(image_path: str) -> str:
        """
        Encode an image file to base64 string.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    @staticmethod
    def decode_base64_to_image(base64_string: str, output_path: str) -> None:
        """
        Decode a base64 string to an image file.
        
        Args:
            base64_string: Base64 encoded image data
            output_path: Path to save the image
        """
        # Handle data URL format if present
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',', 1)[1]
        
        with open(output_path, "wb") as image_file:
            image_file.write(base64.b64decode(base64_string))
    
    def is_available(self) -> bool:
        """
        Check if the API is available.
        
        Returns:
            True if API is reachable, False otherwise
        """
        try:
            self.ping()
            return True
        except:
            return False


# Example usage
if __name__ == "__main__":
    # Initialize client
    api = StableDiffusionAPI("http://127.0.0.1:7860")
    
    # Check if API is available
    if api.is_available():
        print("API is available!")
        
        # Get available models
        models = api.get_sd_models()
        print(f"Available models: {[m['title'] for m in models]}")
        
        # Generate a simple image
        result = api.txt2img(
            prompt="a beautiful sunset over mountains, digital art",
            width=512,
            height=512,
            steps=20,
            cfg_scale=7.0
        )
        
        # Save the first image
        if result.get('images'):
            api.decode_base64_to_image(result['images'][0], "output.png")
            print("Image saved as output.png")
    else:
        print("API is not available. Make sure Stable Diffusion WebUI is running with --api flag.")