import React, { useState, useEffect } from 'react';
import { motion, useSpring, useTransform, useMotionValue } from 'framer-motion';

/**
 * JellySwitch - A high-fidelity jelly switch simulation
 * Simulates the physics and visual properties of a translucent gummy switch
 */
export function JellySwitch({
    checked,
    onChange,
    disabled = false,
    size = 'large'
}) {
    const sizes = {
        small: { width: 70, height: 36, padding: 4 },
        medium: { width: 90, height: 46, padding: 5 },
        large: { width: 120, height: 60, padding: 6 }
    };

    const { width, height, padding } = sizes[size];
    const knobSize = height - (padding * 2);
    const travelDistance = width - knobSize - (padding * 2);

    // Physics springs
    const x = useSpring(checked ? travelDistance : 0, {
        stiffness: 400,
        damping: 25,
        mass: 1.2
    });

    // Derived transforms for jelly deformation
    // Velocity-based stretch
    const velocity = x.getVelocity();
    const scaleX = useTransform(x, (current) => {
        // Stretch when moving fast
        const vel = x.getVelocity();
        // Squash when hitting ends (approximate based on position)
        const isNearEnd = current < 5 || current > travelDistance - 5;
        if (isNearEnd && Math.abs(vel) > 100) {
            return 0.8; // Squash on impact
        }
        return 1 + Math.abs(vel) / 5000; // Stretch on move
    });

    const scaleY = useTransform(scaleX, (sX) => {
        // Conservation of volume: scaleY = 1 / scaleX
        // But we clamp it to avoid extreme thinness
        return Math.max(0.8, 1 / sX);
    });

    const rotate = useTransform(x, (current) => {
        const vel = x.getVelocity();
        return -vel / 200; // Tilt based on velocity
    });

    // Sync spring with checked state
    useEffect(() => {
        x.set(checked ? travelDistance : 0);
    }, [checked, travelDistance, x]);

    return (
        <div
            className="relative inline-block"
            style={{ width, height }}
        >
            {/* Track / Base */}
            <motion.div
                className="absolute inset-0 rounded-full cursor-pointer overflow-hidden"
                onClick={() => !disabled && onChange(!checked)}
                style={{
                    background: '#1a1a1a',
                    boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.1)',
                    border: '1px solid rgba(255,255,255,0.05)'
                }}
            >
                {/* Track Fill */}
                <motion.div
                    className="absolute inset-0 rounded-full"
                    initial={false}
                    animate={{
                        opacity: checked ? 1 : 0,
                        background: 'linear-gradient(90deg, #ef4444 0%, #7f1d1d 100%)'
                    }}
                    transition={{ duration: 0.4 }}
                    style={{
                        boxShadow: 'inset 0 2px 10px rgba(0,0,0,0.3)'
                    }}
                />

                {/* Grid/Texture pattern for depth (optional) */}
                <div
                    className="absolute inset-0 opacity-20"
                    style={{
                        backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)',
                        backgroundSize: '8px 8px'
                    }}
                />
            </motion.div>

            {/* The Jelly Knob */}
            <motion.div
                className="absolute top-0 left-0 cursor-pointer"
                style={{
                    width: knobSize,
                    height: knobSize,
                    x,
                    top: padding,
                    left: padding,
                    scaleX,
                    scaleY,
                    rotate,
                    zIndex: 10
                }}
                onClick={() => !disabled && onChange(!checked)}
                whileTap={{ scale: 0.9 }}
            >
                {/* Main Body - Translucent Gummy Look */}
                <motion.div
                    className="w-full h-full rounded-full relative"
                    style={{
                        background: checked
                            ? 'radial-gradient(circle at 30% 30%, rgba(255, 100, 100, 0.95), rgba(200, 20, 20, 0.9))'
                            : 'radial-gradient(circle at 30% 30%, rgba(200, 200, 200, 0.95), rgba(100, 100, 100, 0.9))',
                        boxShadow: `
              inset 2px 2px 6px rgba(255,255,255,0.4), 
              inset -2px -5px 8px rgba(0,0,0,0.4),
              0 4px 10px rgba(0,0,0,0.3),
              0 10px 20px rgba(0,0,0,0.2)
            `,
                        backdropFilter: 'blur(4px)',
                    }}
                >
                    {/* Specular Highlight (Glossy Reflection) */}
                    <div
                        className="absolute top-[15%] left-[15%] w-[35%] h-[20%] rounded-full bg-white opacity-60 blur-[1px]"
                        style={{ transform: 'rotate(-45deg)' }}
                    />

                    {/* Secondary Highlight */}
                    <div
                        className="absolute bottom-[15%] right-[20%] w-[15%] h-[10%] rounded-full bg-white opacity-20 blur-[2px]"
                        style={{ transform: 'rotate(-45deg)' }}
                    />

                    {/* Inner Glow/Subsurface Scattering simulation */}
                    <div
                        className="absolute inset-[10%] rounded-full"
                        style={{
                            background: checked
                                ? 'radial-gradient(circle at 50% 50%, rgba(255,150,150,0.6), transparent 70%)'
                                : 'radial-gradient(circle at 50% 50%, rgba(255,255,255,0.3), transparent 70%)',
                            filter: 'blur(5px)'
                        }}
                    />
                </motion.div>
            </motion.div>
        </div>
    );
}

export default JellySwitch;
