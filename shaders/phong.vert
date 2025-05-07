#version 330
uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;
layout(location = 0) in vec3 position;
in vec2 vertexUV;
in vec3 vertexNormal;

out vec3 position;
out vec2 UV;
out vec3 normal;

struct Shadow
{
    // direction of light that casts shadow
    vec3 lightDirection;
    // data from camera that produces depth texture
    mat4 projectionMatrix;
    mat4 viewMatrix;
    // texture that stores depth values from shadow camera
    sampler2D depthTexture;
    // regions in shadow multiplied by (1-strength)
    float strength;
    // reduces unwanted visual artifacts
    float bias;
};

uniform bool useShadow;
uniform Shadow shadow0;
out vec3 shadowPosition0;

void main()
{
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1);
    position = vec3( modelMatrix * vec4(vertexPosition, 1) );
    UV = vertexUV;
    normal = normalize( mat3(modelMatrix) * vertexNormal );
    
    if (useShadow)
    {
        vec4 temp0 = shadow0.projectionMatrix * shadow0. viewMatrix * modelMatrix * vec4(vertexPosition, 1);
        shadowPosition0 = vec3( temp0 );
    }
}