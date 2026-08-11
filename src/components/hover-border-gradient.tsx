'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: any[]) { return twMerge(clsx(inputs)) }

type Direction = 'TOP' | 'LEFT' | 'BOTTOM' | 'RIGHT'

const movingMap: Record<Direction, string> = {
  TOP: 'radial-gradient(20.7% 50% at 50% 0%, rgba(236,237,239,0.4) 0%, rgba(76,141,255,0) 100%)',
  LEFT: 'radial-gradient(16.6% 43.1% at 0% 50%, rgba(236,237,239,0.4) 0%, rgba(76,141,255,0) 100%)',
  BOTTOM: 'radial-gradient(20.7% 50% at 50% 100%, rgba(236,237,239,0.4) 0%, rgba(76,141,255,0) 100%)',
  RIGHT: 'radial-gradient(16.2% 41.2% at 100% 50%, rgba(236,237,239,0.4) 0%, rgba(76,141,255,0) 100%)',
}

const highlight = 'radial-gradient(75% 181.2% at 50% 50%, #4c8dff 0%, rgba(76,141,255,0) 100%)'

interface HoverBorderGradientLinkProps {
  href: string
  children: React.ReactNode
  className?: string
  containerClassName?: string
  duration?: number
  clockwise?: boolean
}

export function HoverBorderGradientLink({
  href,
  children,
  className,
  containerClassName,
  duration = 1,
  clockwise = true,
}: HoverBorderGradientLinkProps) {
  const [hovered, setHovered] = useState<boolean>(false)
  const [direction, setDirection] = useState<Direction>('BOTTOM')

  const rotateDirection = (currentDirection: Direction): Direction => {
    const directions: Direction[] = ['TOP', 'LEFT', 'BOTTOM', 'RIGHT']
    const currentIndex = directions.indexOf(currentDirection)
    const nextIndex = clockwise
      ? (currentIndex - 1 + directions.length) % directions.length
      : (currentIndex + 1) % directions.length
    return directions[nextIndex]
  }

  useEffect(() => {
    if (!hovered) {
      const interval = setInterval(() => {
        setDirection((prevState) => rotateDirection(prevState))
      }, duration * 1000)
      return () => clearInterval(interval)
    }
  }, [hovered, duration])

  return (
    <Link
      href={href}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={cn(
        'relative inline-flex h-min w-fit flex-col flex-nowrap content-center items-center justify-center gap-10 overflow-visible rounded-md border border-transparent bg-transparent box-decoration-clone p-px transition duration-500',
        containerClassName
      )}
    >
      <div
        className={cn(
          'z-10 w-auto rounded-[inherit] px-6 py-3 text-sm font-semibold',
          className
        )}
      >
        {children}
      </div>
      <motion.div
        className={cn(
          'absolute inset-0 z-0 flex-none overflow-hidden rounded-md pointer-events-none'
        )}
        style={{
          filter: 'blur(1px)',
          position: 'absolute',
          width: '100%',
          height: '100%',
        }}
        initial={{ background: movingMap[direction] }}
        animate={{
          background: hovered
            ? [movingMap[direction], highlight]
            : movingMap[direction],
        }}
        transition={{ ease: 'linear', duration: duration ?? 1 }}
      />
      <div className='absolute inset-0 z-1 flex-none rounded-md bg-transparent' />
    </Link>
  )
}

export default HoverBorderGradientLink
