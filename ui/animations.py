"""
Animation Utilities — Premium Micro-Interactions
Shared helpers for smooth UI transitions using standard PyQt6 animations.
"""
from PyQt6.QtCore import (
    QObject, QPropertyAnimation, QParallelAnimationGroup, 
    QEasingCurve, Qt, QTimer, QRect, QPoint
)
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect, QSplitter

def animate_splitter(splitter: QSplitter, target_sizes: list[int], duration: int = 250):
    """
    Smoothly animates a QSplitter's sizes from current to target.
    Since QSplitter doesn't support QPropertyAnimation on 'sizes', 
    we use a QTimer to interpolate values manually.
    """
    start_sizes = splitter.sizes()
    if start_sizes == target_sizes:
        return

    # Setup animation state
    steps = duration // 16  # ~60 FPS
    if steps < 1: steps = 1
    
    current_step = 0
    
    def step():
        nonlocal current_step
        current_step += 1
        progress = current_step / steps
        
        # Cubic Ease Out
        t = progress - 1
        ease = t * t * t + 1
        
        new_sizes = []
        for start, end in zip(start_sizes, target_sizes):
            diff = end - start
            val = int(start + (diff * ease))
            new_sizes.append(val)
            
        splitter.setSizes(new_sizes)
        
        if current_step >= steps:
            timer.stop()
            splitter.setSizes(target_sizes) # Ensure final value
            
    timer = QTimer(splitter) # Parent to splitter so it gets cleaned up
    timer.timeout.connect(step)
    timer.start(16)
    
    # Keep reference to avoid GC
    setattr(splitter, "_anim_timer", timer)


def fade_widget(widget: QWidget, start: float, end: float, duration: int = 200, easing=QEasingCurve.Type.OutCubic):
    """
    Fades a widget's opacity.
    Auto-creates QGraphicsOpacityEffect if needed.
    """
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(easing)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


def slide_height(widget: QWidget, start_h: int, end_h: int, duration: int = 200):
    """
    Animates a widget's maximumHeight to slide it open/closed.
    """
    anim = QPropertyAnimation(widget, b"maximumHeight", widget)
    anim.setDuration(duration)
    anim.setStartValue(start_h)
    anim.setEndValue(end_h)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    
    # Ensure visibility logic
    if end_h > 0 and not widget.isVisible():
        widget.setVisible(True)
    
    # Logic to hide after animation if closing
    if end_h == 0:
        anim.finished.connect(lambda: widget.setVisible(False))
        
    return anim


def pulse_button(button: QWidget, duration: int = 200):
    """
    Subtle scale pulse animation for icons/buttons.
    Actually animates geometry very slightly to simulate pulse since 
    transforms are complex on standard widgets.
    """
    start_geo = button.geometry()
    
    # Grow slightly
    w, h = start_geo.width(), start_geo.height()
    grow_w, grow_h = int(w * 1.15), int(h * 1.15)
    
    center = start_geo.center()
    target_rect = QRect(0, 0, grow_w, grow_h)
    target_rect.moveCenter(center)
    
    anim = QPropertyAnimation(button, b"geometry", button)
    anim.setDuration(duration)
    anim.setKeyValueAt(0, start_geo)
    anim.setKeyValueAt(0.5, target_rect)
    anim.setKeyValueAt(1, start_geo)
    anim.setEasingCurve(QEasingCurve.Type.OutQuad)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


def crossfade_theme(window: QWidget, theme_callback, duration: int = 300):
    """
    Visual crossfade for theme switching.
    Dips window opacity slightly, calls the callback (which changes theme),
    then restores opacity.
    """
    anim = QPropertyAnimation(window, b"windowOpacity", window)
    anim.setDuration(duration)
    
    # Dip to 0.92 then back to 1.0
    # We split into two sequential animations or use key values
    anim.setKeyValues([
        (0.0, 1.0),
        (0.4, 0.92), # Point of theme switch
        (1.0, 1.0)
    ])
    
    def on_value_changed(val):
        # Hacky way to trigger swap at the dip
        # In a real property animation we don't get a callback at exactly 0.5 easily
        # So we just do it immediately?? 
        # Better approach:
        # 1. Fade out (half duration) -> Finish -> Swap -> Fade in
        pass
        
    # Better approach for clean code:
    # We will just run the callback immediately but the visual effect 
    # of opacity changing makes it feel smoother.
    # Actually, let's try: Fade Out -> Swap -> Fade In
    
    anim1 = QPropertyAnimation(window, b"windowOpacity", window)
    anim1.setDuration(duration // 2)
    anim1.setStartValue(1.0)
    anim1.setEndValue(0.92)
    anim1.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def on_dip_finished():
        theme_callback()
        anim2 = QPropertyAnimation(window, b"windowOpacity", window)
        anim2.setDuration(duration // 2)
        anim2.setStartValue(0.92)
        anim2.setEndValue(1.0)
        anim2.setEasingCurve(QEasingCurve.Type.InCubic)
        anim2.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        # Keep ref
        setattr(window, "_theme_anim_2", anim2)
        
    anim1.finished.connect(on_dip_finished)
    anim1.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    setattr(window, "_theme_anim_1", anim1)
