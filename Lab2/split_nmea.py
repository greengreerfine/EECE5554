        return int(fields[6])
    except ValueError:
        return None


def hhmmss_to_seconds(v):
    """Convert NMEA HHMMSS.ss numeric value to seconds since midnight."""
    if v is None:
        return None
    hour = int(v // 10000)
    minute = int((v % 10000) // 100)
    second = v % 100
    return hour * 3600 + minute * 60 + second


def duration_seconds(lines):
    times = [parse_utc(x) for x in lines]
    times = [hhmmss_to_seconds(x) for x in times if x is not None]
    if len(times) < 2:
        return 0.0

    start = times[0]
    end = times[-1]




    # Handle UTC midnight rollover.
    if end < start:
        end += 24 * 3600

    return end - start


def in_window(t, start, end):
    if t is None:
        return False

    # These current stationary runs do not cross midnight.
    if start is not None and t < start:
        return False
    if end is not None and t > end:
        return False
    return True


def split_window(name, cfg):
    src = cfg["file"]

    if not src.exists():
        print(f"[MISSING] {src}")
        return

    with src.open("r", errors="ignore") as f:
        gga_lines = [line for line in f if is_gga(line)]

    selected = [
        line for line in gga_lines
        if in_window(parse_utc(line), cfg["start"], cfg["end"])
    ]

    out_file = OUT / f"{name}.nmea"
    out_file.write_text("".join(selected))

    fixes = Counter(parse_fix_quality(x) for x in selected)
    fixes.pop(None, None)

    dur = duration_seconds(selected)
    required = cfg["min_seconds"]

    print(f"\n{name}")
    print("-" * len(name))
    print(f"source      : {src}")
    print(f"output      : {out_file}")
    print(f"GGA epochs  : {len(selected)}")
    print(f"duration    : {dur:.1f} s ({dur/60:.2f} min)")
    print(f"minimum     : {required} s ({required/60:.1f} min)")
    print(f"duration OK : {'YES' if dur >= required else 'NO'}")
    print(f"fix_quality : {dict(sorted(fixes.items()))}")


def summarize_walking_raw():
    if not WALKING_FILE.exists():
        print(f"\n[MISSING] {WALKING_FILE}")
        return

    with WALKING_FILE.open("r", errors="ignore") as f:
        lines = [line for line in f if is_gga(line)]

    fixes = Counter(parse_fix_quality(x) for x in lines)
    fixes.pop(None, None)

    print("\nwalking.nmea (RAW ONLY - NOT SPLIT YET)")
    print("---------------------------------------")
    print(f"GGA epochs  : {len(lines)}")
    print(f"duration    : {duration_seconds(lines):.1f} s")
    print(f"fix_quality : {dict(sorted(fixes.items()))}")
    print("NOTE        : Do not use the whole file yet.")
    print("              We still need to isolate the real 200-300 m moving segment")
    print("              and remove any waiting/stationary tail after the walk.")


def main():
    print(f"Input directory : {DATA}")
    print(f"Output directory: {OUT}")

    for name, cfg in WINDOWS.items():
        split_window(name, cfg)

    summarize_walking_raw()

    print("\nIMPORTANT")
    print("---------")
    print("The raw NMEA files in Lab2/data are never modified.")
    print("The current RTK END times are intentionally left open.")
    print("Next step: inspect the tails and set END times only if the receiver")
    print("kept logging after the real experiment had finished.")


if __name__ == "__main__":
    main()

