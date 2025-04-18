#version 330 core
in vec3 fragColor;
in vec3 fragNormal;

uniform float ambientStrength;
uniform vec3 ambientColor;
uniform vec3 meshColor;
uniform bool useCustomColor;

out vec4 outColor;

void main() {
    // Define light coming from below (pointing downward in world space)
    vec3 lightDir = vec3(0.0, -1.0, 0.0);
    
    // Calculate how much the normal faces the light direction
    // Higher values mean the surface is more facing the light from below
    float dirFactor = max(dot(normalize(fragNormal), lightDir), 0.0);
    
    // Add a small base ambient term to avoid completely dark areas
    float baseFactor = 0.2;
    
    // Calculate directional ambient light (stronger from below)
    vec3 ambient = ambientStrength * ambientColor * (baseFactor + dirFactor);
    
    // Choose between vertex colors or uniform mesh color
    vec3 baseColor = useCustomColor ? meshColor : fragColor;
    
    // Apply lighting to the color
    vec3 result = ambient * baseColor;
    
    outColor = vec4(result, 1.0);
}
