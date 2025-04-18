#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;
layout(location = 2) in vec3 v_norm;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform float time;

out vec3 fragColor;
out vec3 fragNormal;

void main() {
    fragColor = color;
    
    // Transform normal to world space for lighting
    mat3 normalMatrix = mat3(transpose(inverse(model)));
    fragNormal = normalize(normalMatrix * v_norm);
    
    gl_Position = projection * view * model * vec4(position, 1.0);
}
