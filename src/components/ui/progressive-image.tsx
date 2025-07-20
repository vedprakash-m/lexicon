import React, { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';

interface ProgressiveImageProps {
  src: string;
  alt: string;
  placeholder?: string;
  blurhash?: string;
  className?: string;
  sizes?: string;
  loading?: 'lazy' | 'eager';
  priority?: boolean;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

interface IntersectionObserverState {
  isIntersecting: boolean;
  hasIntersected: boolean;
}

export const ProgressiveImage: React.FC<ProgressiveImageProps> = ({
  src,
  alt,
  placeholder,
  blurhash,
  className,
  sizes = '100vw',
  loading = 'lazy',
  priority = false,
  onLoad,
  onError
}) => {
  const [imageState, setImageState] = useState<'loading' | 'loaded' | 'error'>('loading');
  const [actualSrc, setActualSrc] = useState<string>('');
  const [intersection, setIntersection] = useState<IntersectionObserverState>({
    isIntersecting: false,
    hasIntersected: false
  });
  
  const imgRef = useRef<HTMLImageElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Generate responsive image URLs
  const generateResponsiveUrls = useCallback((baseSrc: string) => {
    if (!baseSrc) return { src: '', srcSet: '' };
    
    const widths = [320, 640, 768, 1024, 1280, 1920];
    const srcSet = widths
      .map(width => {
        // Assume we have an image processing service or CDN
        const responsiveUrl = baseSrc.includes('?') 
          ? `${baseSrc}&w=${width}&q=80&format=webp`
          : `${baseSrc}?w=${width}&q=80&format=webp`;
        return `${responsiveUrl} ${width}w`;
      })
      .join(', ');
    
    return {
      src: baseSrc.includes('?') 
        ? `${baseSrc}&w=1024&q=80&format=webp`
        : `${baseSrc}?w=1024&q=80&format=webp`,
      srcSet
    };
  }, []);

  // Intersection Observer setup
  useEffect(() => {
    if (priority || loading === 'eager') {
      // Load immediately for priority images
      setIntersection({ isIntersecting: true, hasIntersected: true });
      return;
    }

    const options = {
      root: null,
      rootMargin: '50px', // Start loading 50px before entering viewport
      threshold: 0.1
    };

    observerRef.current = new IntersectionObserver((entries) => {
      const entry = entries[0];
      if (entry.isIntersecting) {
        setIntersection(prev => ({
          isIntersecting: true,
          hasIntersected: true
        }));
        // Disconnect observer after first intersection
        observerRef.current?.disconnect();
      }
    }, options);

    if (imgRef.current) {
      observerRef.current.observe(imgRef.current);
    }

    return () => {
      observerRef.current?.disconnect();
    };
  }, [priority, loading]);

  // Load image when in viewport
  useEffect(() => {
    if (intersection.hasIntersected && src && imageState === 'loading') {
      const { src: responsiveSrc } = generateResponsiveUrls(src);
      
      // Preload the image
      const img = new Image();
      
      img.onload = () => {
        setActualSrc(responsiveSrc);
        setImageState('loaded');
        onLoad?.();
      };
      
      img.onerror = (event) => {
        setImageState('error');
        const error = new Error(`Failed to load image: ${src}`);
        onError?.(error);
      };
      
      img.src = responsiveSrc;
    }
  }, [intersection.hasIntersected, src, imageState, generateResponsiveUrls, onLoad, onError]);

  // Generate placeholder image (low quality or blur hash)
  const getPlaceholderSrc = useCallback(() => {
    if (placeholder) return placeholder;
    
    if (blurhash) {
      // In a real implementation, you'd decode the blurhash
      // For now, return a simple data URL
      return `data:image/svg+xml;base64,${btoa(`
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
          <rect width="100%" height="100%" fill="#f0f0f0"/>
          <text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#999">
            Loading...
          </text>
        </svg>
      `)}`;
    }
    
    // Generate low-quality placeholder from main src
    if (src) {
      return src.includes('?') 
        ? `${src}&w=20&q=20&blur=5`
        : `${src}?w=20&q=20&blur=5`;
    }
    
    return '';
  }, [placeholder, blurhash, src]);

  const { src: responsiveSrc, srcSet } = generateResponsiveUrls(actualSrc);
  const placeholderSrc = getPlaceholderSrc();

  return (
    <div className={cn("relative overflow-hidden", className)}>
      {/* Placeholder Image */}
      {placeholderSrc && imageState === 'loading' && (
        <img
          src={placeholderSrc}
          alt=""
          className={cn(
            "absolute inset-0 w-full h-full object-cover transition-opacity duration-500",
            "filter blur-sm scale-105", // Slight blur and scale to hide edges
            intersection.hasIntersected ? "opacity-100" : "opacity-0"
          )}
          aria-hidden="true"
        />
      )}

      {/* Loading Skeleton */}
      {!intersection.hasIntersected && (
        <div 
          className="absolute inset-0 bg-muted animate-pulse"
          aria-hidden="true"
        />
      )}

      {/* Main Image */}
      <img
        ref={imgRef}
        src={responsiveSrc}
        srcSet={srcSet}
        sizes={sizes}
        alt={alt}
        className={cn(
          "w-full h-full object-cover transition-opacity duration-500",
          imageState === 'loaded' ? "opacity-100" : "opacity-0"
        )}
        loading={loading}
        decoding="async"
        style={{
          // Prevent layout shift
          aspectRatio: 'var(--aspect-ratio, auto)',
        }}
      />

      {/* Error State */}
      {imageState === 'error' && (
        <div className="absolute inset-0 bg-muted flex items-center justify-center">
          <div className="text-center text-muted-foreground">
            <svg
              className="w-8 h-8 mx-auto mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <p className="text-sm">Failed to load image</p>
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {imageState === 'loading' && intersection.hasIntersected && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
};

// High-level component for book covers and thumbnails
interface BookCoverImageProps extends Omit<ProgressiveImageProps, 'src'> {
  bookId: string;
  coverUrl?: string;
  title: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const BookCoverImage: React.FC<BookCoverImageProps> = ({
  bookId,
  coverUrl,
  title,
  size = 'md',
  className,
  ...props
}) => {
  const sizeClasses = {
    sm: 'w-12 h-16',
    md: 'w-16 h-24',
    lg: 'w-24 h-36',
    xl: 'w-32 h-48'
  };

  const aspectRatios = {
    sm: '3/4',
    md: '2/3',
    lg: '2/3',
    xl: '2/3'
  };

  // Generate placeholder for book covers
  const generateBookPlaceholder = useCallback(() => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-red-500',
      'bg-indigo-500',
      'bg-pink-500'
    ];
    
    const colorIndex = bookId.charCodeAt(0) % colors.length;
    const bgColor = colors[colorIndex];
    
    return `data:image/svg+xml;base64,${btoa(`
      <svg width="200" height="300" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" class="${bgColor}" fill="#6366f1"/>
        <text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="white" 
              font-family="system-ui" font-size="12" font-weight="600">
          ${title.substring(0, 20)}${title.length > 20 ? '...' : ''}
        </text>
      </svg>
    `)}`;
  }, [bookId, title]);

  return (
    <div 
      className={cn(sizeClasses[size], className)}
      style={{ '--aspect-ratio': aspectRatios[size] } as React.CSSProperties}
    >
      <ProgressiveImage
        src={coverUrl || ''}
        alt={`Cover of ${title}`}
        placeholder={generateBookPlaceholder()}
        className="rounded-md shadow-md"
        loading="lazy"
        sizes={`(max-width: 768px) ${size === 'sm' ? '50px' : size === 'md' ? '80px' : '120px'}, ${size === 'xl' ? '200px' : '150px'}`}
        {...props}
      />
    </div>
  );
};

// Image gallery component with lazy loading
interface ImageGalleryProps {
  images: Array<{ src: string; alt: string; id: string }>;
  className?: string;
  columns?: number;
}

export const ImageGallery: React.FC<ImageGalleryProps> = ({
  images,
  className,
  columns = 3
}) => {
  return (
    <div 
      className={cn(
        "grid gap-4",
        `grid-cols-${Math.min(columns, 4)}`,
        className
      )}
      style={{
        gridTemplateColumns: `repeat(${columns}, 1fr)`
      }}
    >
      {images.map((image, index) => (
        <div
          key={image.id}
          className="aspect-square"
          style={{ '--aspect-ratio': '1' } as React.CSSProperties}
        >
          <ProgressiveImage
            src={image.src}
            alt={image.alt}
            className="rounded-lg"
            loading={index < 6 ? 'eager' : 'lazy'}
            priority={index < 3}
            sizes={`(max-width: 768px) 50vw, ${100 / columns}vw`}
          />
        </div>
      ))}
    </div>
  );
};
