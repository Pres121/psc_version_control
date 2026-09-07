import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/update_response.dart';

/// Shows the appropriate PSC update dialog for [info].
/// Does nothing if no update is available.
Future<void> showPscUpdateDialog(
  BuildContext context, {
  required String appName,
  required PscUpdateInfo info,
}) async {
  if (!info.updateAvailable && !info.updateRequired) return;

  await showDialog(
    context: context,
    barrierDismissible: !info.updateRequired,
    builder: (context) => PopScope(
      canPop: !info.updateRequired,
      child: AlertDialog(
        title: Text(
          info.updateRequired ? '⚠️ Update Required' : '🚀 New version available',
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              info.updateRequired
                  ? 'Your version of $appName is no longer supported.\n\n'
                      'Please update to continue using the application.'
                  : '$appName ${info.latestVersion ?? ''} is now available.',
            ),
            if (!info.updateRequired && info.releaseNotes.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text("What's new:", style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              ...info.releaseNotes.map((note) => Text('• $note')),
            ],
          ],
        ),
        actions: [
          if (!info.updateRequired)
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Later'),
            ),
          FilledButton(
            onPressed: () async {
              if (info.updateUrl != null) {
                final uri = Uri.parse(info.updateUrl!);
                if (await canLaunchUrl(uri)) {
                  await launchUrl(uri, mode: LaunchMode.externalApplication);
                }
              }
              if (!info.updateRequired && context.mounted) {
                Navigator.of(context).pop();
              }
            },
            child: const Text('Update Now'),
          ),
        ],
      ),
    ),
  );
}
